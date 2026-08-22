# Phase 19 Tier 2 Classical Colocalization Recovery Plan

## Decision and purpose

Execution status: completed locally on 2026-08-21. The validated 26-file bundle
is under `results/minerva_production/19_genetic_support_tier2_recovery/`; exact
route outcomes, source acquisition, validation, and remaining access gaps are
recorded in the [execution report](tier2_recovery_execution_report.md).

This document defines the follow-up needed to fix the scientific limitations
identified by the completed Tier 2 regional source/model audit. It is a new,
local-first analysis increment. It does not replace or rewrite either of the
validated result bundles:

```text
results/minerva_production/19_genetic_support/
results/minerva_production/19_genetic_support_tier2/
```

The completed Tier 2 analysis found useful AD GWAS and QTL fine-mapping data,
but none of the 54 nuclear eQTL/sQTL routes had all inputs required for a valid
classical colocalization calculation. In plain terms, the analysis could see
variants associated with Alzheimer disease and could see selected variants
associated with gene regulation, but it could not compare the two complete
regional patterns using compatible statistical models and ancestry-matched
correlation information. Therefore, `not_assessable` meant “the comparison
could not be calculated reliably,” not “the two traits do not share a causal
variant.”

This recovery increment will obtain the missing inputs route by route, run
compatible fine-mapping and classical H0-H4 colocalization where scientifically
valid, and replace generic `not_assessable` labels with either a resolved result
or a precise, source-specific terminal limitation.

Where this plan is silent, the
[Phase 19 master plan](human_genetic_support_plan.md) and the
[Tier 2 regional plan](tier2_regional_gwas_qtl_plan.md) remain authoritative.

## Frozen starting point

The validated Tier 2 bundle records:

```text
validation_status = validated_complete_tier2_regional_coloc
candidate_contexts = 47
unique_genes = 25
nuclear_genes = 19
nuclear_candidate_contexts = 27
base_eqtl_sqtl_route_units = 54
qtl_finemapping_rows = 9363
dense_candidate_region_gwas_rows = 311180
classical_h0_h4_resolved_routes = 0
not_assessable_routes = 54
```

The 54 routes split into four recovery strata:

| Recovery stratum | Routes | Required next action |
|---|---:|---|
| Exact cell-context eQTL | 24 | Obtain dense QTL statistics or reusable source model and compatible LD. |
| Bulk-brain fallback eQTL | 3 | Obtain dense bulk-brain QTL statistics/model and retain the fallback label. |
| Bulk-brain fallback sQTL | 25 | Obtain dense event-level sQTL statistics/model and verify event-to-gene mapping. |
| LAMTOR5 sQTL not represented in the release | 2 | Determine whether the context measured a valid LAMTOR5 splicing event; then acquire statistics or end with a specific terminal state. |

Twenty-two routes include at least one released QTL CS95 row. A credible-set
row alone is not sufficient for H0-H4 colocalization because it omits the
likelihood pattern for the other variants in the region. The recovery must use
full regional statistics or complete compatible fine-mapping model objects.

## Recovery question and possible outcomes

For each frozen route, the recovery asks:

> After matching the phenotype, molecular trait, context, genome build,
> ancestry, alleles, region, variants, model, and LD, do the AD GWAS and the
> eQTL or sQTL support the same causal signal?

The recovery can legitimately produce any of these findings:

- strong evidence that an AD and molecular-QTL signal are shared;
- evidence that both signals exist but are distinct;
- no detectable AD signal in the frozen region;
- no detectable QTL signal in the frozen region;
- the molecular trait was not measured in the required context;
- the available model or LD remains incompatible; or
- the comparison remains unassessable for a named data-access reason.

The goal is to make every attempt reproducible and every limitation precise.
It is not scientifically realistic to require all 54 routes to become positive
or even calculable.

## Frozen scientific rules

The following rules are inherited without result-dependent changes:

```text
primary_method = coloc.susie
single_signal_sensitivity = coloc.abf
p1 = 1e-4
p2 = 1e-4
p12_primary = 5e-6
p12_sensitivity = 1e-6,5e-6,1e-5
shared_signal_threshold = PP.H4 >= 0.80
conditional_shared_threshold = PP.H4 / (PP.H3 + PP.H4) >= 0.80
credible_set_coverage = 0.95
custom_susie_L = 10
custom_susie_maxit = 1000
```

`coloc.susie` is the primary method because more than one causal signal can
occur in a locus. `coloc.abf` may be reported only as a prespecified
single-signal sensitivity. PIP values, credible-set membership, lead-variant
overlap, or significance overlap must never be renamed as H4.

The Bellenguez Alzheimer disease GWAS is a case-control study. Custom models
must preserve that data type and record the case fraction as
`s = cases / (cases + controls)`; it must not be analyzed as a quantitative
trait.

## Data acquisition strategy

### 1. Dense molecular-QTL statistics

The primary targeted source will be the EMBL-EBI eQTL Catalogue:

- data access: <https://www.ebi.ac.uk/eqtl/Data_access/>;
- API documentation: <https://www.ebi.ac.uk/eqtl/api/docs>.

For every selected dataset, freeze all of the following before inspecting its
result:

```text
catalogue release
study identifier
dataset identifier
tissue or cell context
eQTL or sQTL method
molecular-trait identifier and annotation release
sample size
reported ancestry or cohort composition
genome build
effect and non-effect allele convention
source file class
availability of SuSiE/LBF model objects
source URL, byte count, and checksum
```

Use the Catalogue API or indexed regional files to discover and validate a
source. Requests must cover the full prespecified candidate region and must not
be filtered by P value, PIP, or credible-set membership. If several candidate
regions come from the same dataset, download the relevant immutable source file
once and perform indexed extraction locally. This avoids fragile repeated FTP
range requests and respects the Catalogue warning that excessive partial-file
requests can be blocked.

The already registered NIAGADS `NG00184.v1` release remains the second route.
Its released QTL fine-mapping objects can be used directly only when they
contain the complete likelihood/model information expected by `coloc.susie`.
The significant-only gene endpoint and the current candidate credible-set
extract remain coverage evidence only.

If targeted public statistics are unavailable, the complete NIAGADS molecular
QTL archives may be downloaded to a local external disk after a storage gate.
The eQTL, sQTL, and single-nucleus eQTL association archives together are about
821 GB. Sequential acquisition and processing requires approximately 1.1 TB
free under the 2.2-times-largest-file safety rule; retaining all source
archives, indexes, extracts, and working files at once is expected to require
about 1.9 TB. This is optional and is not a reason to run on Minerva.

No dense QTL input may be reconstructed from significant-only rows. If neither
a dense regional source nor a complete source model is available, the route
ends with the exact unavailable-source reason.

### 2. AD GWAS statistics and model

Reuse the frozen, checksum-validated GWAS Catalog Bellenguez 2022 statistics:

```text
study = GCST90027158
build = GRCh38
source role = primary late-onset AD GWAS
```

The existing 311,180 candidate-region rows are reusable after their immutable
hashes pass. Fine-map each unique GWAS locus once and reference that result from
every relevant QTL route. Before modeling, confirm sample size, case count,
control count, ancestry, beta/log-odds interpretation, standard error, allele
frequency, and effect-allele direction from the study metadata.

If the released AD fine-mapping model is compatible with the chosen molecular
model and variant space, prefer it. Otherwise run the frozen custom SuSiE-RSS
model using full, unfiltered regional GWAS statistics and an approved LD panel.

### 3. Ancestry-compatible LD

LD describes which nearby variants tend to be inherited together. An LD panel
from a mismatched population can make fine-mapping select the wrong variant.
Use this prespecified order:

1. the LD or complete model released with the analyzed source;
2. NIAGADS `NG00067` ADSP WGS R5 non-Hispanic White panel, `n = 26,042`, for a
   compatible predominantly European AD comparison;
3. the unrelated European subset of the 1000 Genomes 30x GRCh38 release as a
   labeled sensitivity;
4. `model_or_ld_incompatible` when no defensible panel is available.

The GWAS and QTL models need not use the identical participant cohort, but each
model must use LD compatible with its own ancestry. A released QTL likelihood
or SuSiE model retains the source study's own LD assumptions. A custom QTL
fine-map requires a separate QTL-ancestry-matched LD source; the ADSP GWAS LD
must not automatically be reused for a differently composed QTL cohort.

Download only the chromosome block or candidate-region variants required by a
route that has already passed the GWAS and QTL input gates. Record panel,
ancestry, sample count, build, extraction command, variant order, checksum, and
all substitutions.

## Context and dataset selection

Dataset selection must be frozen without looking at whether colocalization is
positive. Apply the following hierarchy separately for eQTL and sQTL:

1. exact displayed cell type or a directly equivalent annotated cell class;
2. a prespecified lineage-level context;
3. bulk brain as an explicitly labeled fallback;
4. `qtl_context_not_measured` when no defensible context exists.

If multiple independent cohorts exist at the same match level, retain all of
them as separate analyses. Do not choose the cohort with the most favorable H4.
Dataset priority may be based on context match, ancestry compatibility, sample
size, completeness, and model availability, but those criteria must be frozen
in `recovery_dataset_registry.tsv` before result calculation.

An exact cell-context result and a bulk-brain fallback result are not
interchangeable. The final summary must retain `context_match_level` and must
not silently promote a bulk result to cell-type-specific evidence.

## LAMTOR5 sQTL decision path

The two missing routes require their own pre-result audit:

```text
gene_symbol = LAMTOR5
gene_id = ENSG00000134248
routes = excitatory_neuron_sQTL, inhibitory_neuron_sQTL
```

For each relevant brain-splicing dataset:

1. inspect the dataset's LeafCutter, txrevise, intron-cluster, or transcript
   event annotation;
2. map the event to GRCh38 and the frozen gene annotation;
3. require that the event genuinely belongs to LAMTOR5 rather than merely
   overlapping its locus;
4. check whether the exact neuronal context assayed the event;
5. if exact context is absent, apply the prespecified bulk-brain fallback;
6. if a complete dense regional test shows no LAMTOR5 splicing association,
   end as `no_regional_qtl_signal`;
7. if the event was not measured or cannot be assigned unambiguously, end as
   `qtl_context_not_measured` or `model_or_ld_incompatible`.

Absence from a significant-only table or credible-set file is not enough to
claim `no_regional_qtl_signal`.

## Route decision matrix

| Available inputs | Action | Permitted terminal state |
|---|---|---|
| Compatible released GWAS and QTL signal models | Run all signal-pair `coloc.susie` comparisons. | `precomputed_resolved` |
| Custom GWAS model plus compatible released QTL model | Harmonize model variant space and run `coloc.susie`. | `custom_resolved` |
| Full GWAS and QTL statistics plus ancestry-compatible LD for both | Fine-map both traits and run all signal pairs. | `custom_resolved` |
| Dense single-signal inputs only | Run `coloc.abf` as sensitivity; do not present it as the multi-signal primary result. | `not_assessable` for the primary route, with sensitivity recorded |
| Complete regional GWAS but no regional AD signal | Stop before interpreting QTL overlap. | `no_regional_gwas_signal` |
| Complete regional QTL but no QTL signal for the frozen molecular trait | Stop before colocalization. | `no_regional_qtl_signal` |
| Signals in both traits but supported as distinct | Record H3/H4 evidence and sensitivity. | `distinct_signals` |
| Trait/context was not measured | Do not substitute an unregistered context. | `qtl_context_not_measured` |
| Build, alleles, ancestry, models, or LD cannot be made compatible | Do not calculate a misleading posterior. | `model_or_ld_incompatible` |
| Required controlled or public source remains unavailable | Preserve exact source and access reason. | `not_assessable` |

## Variant and model compatibility gates

Every custom route must pass all gates before fine-mapping or colocalization:

- both traits use GRCh38 coordinates, or a validated one-to-one lift-over with
  original and lifted coordinates retained;
- chromosome naming and positions are normalized;
- variants have a stable `chromosome:position:reference:alternate` identity;
- effect alleles are aligned and effect directions are transformed when
  required;
- palindromic A/T and C/G variants with ambiguous frequency are removed;
- duplicated positions, multiallelic variants, allele conflicts, and invalid
  standard errors are resolved deterministically;
- allele frequencies agree within the prespecified tolerance, with mismatches
  reported rather than silently discarded;
- the common variant set meets the frozen count and regional-coverage gates;
- the LD matrix uses exactly the same variants in exactly the same order;
- LD is symmetric, finite, positive semidefinite after only a documented
  numerical correction, and has a unit diagonal;
- the summary-statistic/LD consistency diagnostic passes; and
- sample-overlap assumptions and source-model covariates are recorded.

The pipeline must emit counts before and after every filter. A low overlap or
failed LD diagnostic is a terminal scientific incompatibility, not an invitation
to tune filters until a result appears.

## Fine-mapping and colocalization workflow

### GWAS fine-mapping

- Define each locus from the frozen candidate-region rule in the original Tier
  2 plan and include the complete dense GWAS region.
- Analyze the GWAS as case-control and record `s`.
- Run one model per unique AD locus, not one copy per displayed context.
- Use `L = 10`, 95% credible sets, and `maxit = 1000` unless a compatible
  released source model has a separately frozen specification.
- Record convergence, prior variance, residual diagnostics, credible sets,
  purity, PIP, and excluded variants.

### QTL fine-mapping

- Prefer released likelihood/SuSiE objects that preserve the full model and
  source LD.
- Otherwise use full unfiltered regional beta, standard error, allele
  frequency, sample size, molecular-trait mapping, and QTL-compatible LD.
- Model each cohort, context, molecular trait, and event independently.
- Never use a significant-only gene table as the model input.

### Colocalization

- Compare every supported GWAS signal with every supported QTL signal using
  `coloc.susie`.
- Retain H0, H1, H2, H3, and H4 posteriors and the conditional H4 statistic.
- Run the frozen `p12` sensitivity values.
- Report all signal pairs; the summary may identify the strongest registered
  pair but must not discard discordant pairs.
- Treat independent cohort and context results as separate evidence, not as
  duplicated votes.

## Local execution and storage contract

No Minerva run is required. Execute directly on the local workstation and
publish the validated final bundle under the repository's existing
`minerva_production` namespace. The manifest must say that the actual backend
was local direct execution.

Use this ignored source root:

```text
data/reference/phase19_genetic_support/tier2_recovery/
  inventory/
  eqtl_catalogue/
  regional_qtl/
  released_qtl_models/
  gwas_models/
  ld_source/
  ld_candidate_blocks/
  source_manifest/
```

Local resource controls:

```text
execution_stage = local_production_equivalent
execution_backend = direct
publication_namespace = minerva_production
max_workers = 1
minimum_free_space_after_task = 50 GiB
planned_working_memory_per_locus = 8 GiB
hard_memory_limit_per_locus = 16 GiB
process_one_locus_at_a_time = TRUE
deterministic_gzip_mtime = 0
```

Before a large download, require free space of at least 2.2 times the largest
compressed source file plus the 50 GiB reserve. If this fails, use an external
local disk or stop with a documented resource limitation. Do not silently move
the analysis to Minerva.

Credentials must be read from environment variables or user configuration and
must never be written to the repository, logs, manifests, commands captured in
reports, or result files.

## Implementation isolation

Add recovery-specific code and configuration so the two validated bundles stay
reproducible:

```text
config/phase19_genetic_support_tier2_recovery.yml
config/phase19_tier2_recovery_local_execution.yml
scripts/19_inventory_tier2_recovery_sources.py
scripts/19_download_tier2_recovery_qtl.py
scripts/19_extract_tier2_recovery_qtl_models.py
scripts/19_extract_tier2_recovery_dense_qtl.py
scripts/19_prepare_tier2_recovery_ld.py
scripts/19_run_genetic_support_tier2_recovery.R
tests/test_phase19_genetic_support_tier2_recovery.R
tests/fixtures/phase19_tier2_recovery/
docs/phase_19_genetic_support/tier2_recovery_execution_report.md
```

Only shared pipeline dispatch and configuration registration may be modified in
place. The recovery must not write into the existing Tier 1 or Tier 2 result or
source directories.

## Execution tasks

### Task 1: Freeze and validate the handoff

1. Read the existing Tier 1 and Tier 2 manifests and status files.
2. Reproduce all registered artifact hashes.
3. Generate exactly 54 recovery routes from the frozen 27 nuclear contexts.
4. Copy identifiers and references, not source files, into the recovery
   manifest.
5. Abort on any baseline mutation or route-count drift.

### Task 2: Build the source inventory

1. Query the eQTL Catalogue metadata for matching brain eQTL and sQTL datasets.
2. Register exact, lineage, and bulk-brain candidates separately.
3. Determine dense-statistic and source-model availability without screening
   on the resulting association strength.
4. Register cohort ancestry, sample size, build, annotation, and file hashes.
5. Freeze one or more eligible sources per context-match level.

### Task 3: Acquire deterministic regional QTL inputs

1. Download or index immutable source files.
2. Extract full candidate regions without P-value filtering.
3. Validate row counts, column types, identifiers, coordinates, and checksums.
4. Re-run extraction and require byte-identical or hash-identical outputs.
5. Record a precise terminal reason when acquisition fails.

### Task 4: Resolve ancestry and LD

1. Match the AD GWAS and each QTL cohort to defensible LD sources.
2. Acquire only candidate blocks after upstream data gates pass.
3. Normalize variants and construct matrices in the harmonized order.
4. Run ancestry, symmetry, eigenvalue, diagonal, and allele-frequency checks.
5. Reject a route when an ancestry-compatible panel cannot be justified.

### Task 5: Harmonize variants and molecular traits

1. Normalize build, coordinates, alleles, and identifiers.
2. Resolve eQTL gene IDs and sQTL event-to-gene mappings.
3. Remove ambiguous or conflicting variants using frozen rules.
4. Emit full audit counts and hashes.
5. Require sufficient common variants and regional coverage.

### Task 6: Fine-map eligible traits

1. Fine-map each unique AD locus once.
2. Reuse complete compatible released QTL models when available.
3. Fine-map QTLs only from complete dense statistics and matched LD.
4. Require convergence and signal/credible-set QC.
5. Preserve failed models with diagnostics and a terminal route state.

### Task 7: Run classical colocalization

1. Run all compatible signal-pair `coloc.susie` comparisons.
2. Run the prespecified prior sensitivity.
3. Run `coloc.abf` only where its single-signal assumptions and input gates
   hold, labeling it as sensitivity.
4. Record H0-H4, conditional H4, signal IDs, method, priors, and warnings.
5. Assign route outcomes using fixed thresholds.

### Task 8: Integrate without overwriting prior evidence

1. Start from the frozen Tier 1 grade and Tier 2 audit result.
2. Add the recovery evidence as a new provenance layer.
3. Upgrade or downgrade no result based only on significant variants, PIP,
   credible-set overlap, or a context fallback.
4. Keep mtDNA, rare-variant, and nuclear-QTL scopes distinct.
5. Keep `full_phase19_complete = FALSE` unless their separate plans complete.

### Task 9: Validate figures and summaries

1. Regenerate the 47-row cumulative evidence matrix.
2. Make route and source strata visible in all summaries.
3. Plot H3 and H4 together so shared and distinct signals are distinguishable.
4. Label exact, lineage, and bulk-brain contexts explicitly.
5. Show unassessable reasons rather than converting them to zero evidence.

### Task 10: Publish atomically

1. Write to a staging directory.
2. Run the complete validation suite.
3. Freeze artifact hashes and the declared output contract.
4. Rename staging to the final directory only after all blocking checks pass.
5. Record the local host and direct backend truthfully.

## Pilot before production

Run a four-part local pilot before scaling across all routes:

1. one exact cell-context eQTL route with dense data;
2. one bulk-brain sQTL fallback route with a validated event mapping;
3. one LAMTOR5 sQTL route through the measurement decision path; and
4. synthetic shared-signal, distinct-signal, allele-flip, LD-order, and
   ancestry-incompatibility controls.

The pilot passes only if it recovers the expected synthetic H4 and H3 patterns,
rejects corrupted/mismatched inputs, reproduces deterministic artifacts, and
does not change either validated baseline bundle.

## Output contract

Pilot output:

```text
results/local_pilot/19_genetic_support_tier2_recovery/
```

Validated local production output:

```text
results/minerva_production/19_genetic_support_tier2_recovery/
```

The final directory contains exactly these 26 declared files:

```text
recovery_analysis_manifest.tsv
recovery_route_manifest.tsv
recovery_dataset_registry.tsv
recovery_request_manifest.tsv
recovery_input_inventory.tsv
recovery_source_checks.tsv
recovery_route_decisions.tsv
recovery_regional_gwas_summary.tsv
recovery_regional_qtl_summary.tsv
recovery_gwas_finemapping.tsv.gz
recovery_qtl_finemapping.tsv.gz
recovery_ld_qc.tsv
recovery_variant_harmonization.tsv.gz
recovery_variant_harmonization_summary.tsv
recovery_colocalization.tsv.gz
recovery_colocalization_qc.tsv
recovery_prior_sensitivity.tsv.gz
recovery_assessability.tsv
recovery_evidence_summary.tsv
recovery_figure_data.tsv.gz
recovery_evidence_matrix.pdf
recovery_evidence_matrix.png
recovery_locus_plots.pdf
recovery_checks.tsv
recovery_artifacts.tsv
recovery_status.tsv
```

No undeclared sidecars, temporary files, credentials, caches, or logs may be
present in the final directory.

## Required tests

The automated test suite must cover:

- immutable handoff hashes and exact 54-route construction;
- source registry schema, stable identifiers, and checksum validation;
- rejection of significant-only QTL inputs as custom-model data;
- full-region extraction without P-value filtering;
- eQTL gene and sQTL event mapping, including LAMTOR5;
- GRCh38 normalization, allele swaps, strand ambiguity, duplicates, and
  multiallelic variants;
- case-control sample fraction and GWAS effect-scale handling;
- ancestry and LD-source compatibility;
- LD order, symmetry, diagonal, finiteness, eigenvalues, and summary/LD
  consistency;
- deterministic SuSiE convergence and credible-set outputs;
- synthetic shared-signal and distinct-signal colocalization;
- all H0-H4 posteriors and prior-sensitivity rows;
- exact versus fallback context labels;
- route decision precedence and terminal-state completeness;
- exactly 47 evidence-summary rows and 54 route outcomes;
- exact 26-file output contract and artifact hashes;
- zero mutation of the two baseline result bundles; and
- truthful local execution metadata with `full_phase19_complete = FALSE`.

## Blocking gates

Publication is forbidden if any of these conditions occurs:

- baseline artifact hashes change;
- the route manifest does not contain exactly 54 frozen routes;
- a custom model uses significant-only or P-value-filtered QTL data;
- a trait is assigned the wrong quantitative/case-control type;
- the build, alleles, molecular trait, or sQTL event cannot be resolved;
- the selected LD is ancestry-incompatible or its variant order differs;
- a model fails convergence or mandatory diagnostic thresholds;
- an H4 label is inferred from PIP, credible-set, or lead-variant overlap;
- the selection of source, context, prior, region, or method depends on the
  observed H4 result;
- a bulk-brain result is labeled as exact cell-context evidence;
- a route lacks a terminal decision and reason;
- an output file is missing, undeclared, or has the wrong schema;
- credentials or access tokens appear in an artifact or log;
- either baseline result directory is modified; or
- any blocking test in `recovery_checks.tsv` fails.

## Completion criteria

Technical completion requires:

```text
validation_status = validated_complete_tier2_classical_coloc_recovery
baseline_tier1_hashes_unchanged = TRUE
baseline_tier2_hashes_unchanged = TRUE
nuclear_recovery_routes = 54
terminal_recovery_routes = 54
cumulative_summary_rows = 47
declared_output_files = 26
undeclared_output_files = 0
blocking_check_failures = 0
execution_backend = direct
full_phase19_complete = FALSE
```

Each route must end in exactly one terminal state:

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

Completion does not require a positive colocalization result. It requires that
all registered recovery attempts are made under compatible inputs, that every
route has a precise and scientifically honest outcome, and that all output and
reproducibility gates pass.

## Recommended execution order

1. Freeze baseline hashes and the 54-route recovery manifest.
2. Inventory targeted eQTL Catalogue datasets and LAMTOR5 event coverage.
3. Run the four-part local pilot.
4. Acquire dense regional QTL inputs in small deterministic batches.
5. Prepare ancestry-compatible LD only for routes that pass upstream gates.
6. Fine-map each unique locus and run all valid signal-pair comparisons.
7. Validate, render, and publish the 26-file local production bundle.
8. Write the recovery execution report with resolved counts and remaining
   source-specific limitations.
