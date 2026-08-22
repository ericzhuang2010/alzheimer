# Phase 19 OPC RPS15 Public-Data-First Recovery Plan

**Status:** approved design; not yet executed  
**Plan date:** 2026-08-21  
**Small-data amendment:** 2026-08-21\
**Primary target:** OPC `RPS15` (`GS045`, `ENSG00000115268`)  
**Secondary context control:** inhibitory-neuron `RPS15` (`GS044`)  
**Execution model:** local production-equivalent; Minerva is not required  
**Author-data dependency:** none  
**Planned publication directory:**  
`/home/ericzhuang2010/VscodeProjects/alzheimer/results/minerva_production/19_genetic_support_opc_rps15_public_recovery/`

## Executive decision

The next Phase 19 workstream will determine how far the unresolved
AD-diagnosis GWAS/QTL evidence for OPC `RPS15` can be resolved using public
data already downloaded or publicly obtainable without investigator
coordination.

The workstream must not wait for an author response. Author outreach may be
recorded as an optional parallel activity, but:

- it is not an input requirement;
- it is not a blocking gate;
- no task has a “wait for author” state;
- technical completion does not depend on receiving a reply; and
- an unavailable model or LD panel becomes an explicit terminal result.

The main public-data route is a result-blind audit of the already-downloaded
ADSP FunGen xQTL Atlas `NG00184.v1` files for `RPS15`. The audit will test
OPC-matched, inhibitory-neuron, lineage, and bulk-brain fallback evidence
without promoting one context into another. It will consider eQTL,
single-nucleus eQTL, sQTL, and brain pQTL as separate routes.

This plan uses a strict small-data policy. Freezing the source scope means
freezing the allowed source registry, contexts, thresholds, and stopping rules;
it does **not** mean downloading every registered source. No full `all` archive
may be downloaded during this workstream. The initial audit uses only files
already present locally. A new public file is eligible only when it is a
complete target-, locus-, chromosome-, or context-specific extract no larger
than 5 GiB, and all new files together may not exceed 10 GiB.

The existing EQTL Catalogue result remains part of the evidence:

- the AD-diagnosis GWAS has a strong regional `RPS15` signal;
- bulk-neocortex `RPS15` eQTL statistics contain a qualifying signal; but
- the released QTL fine-mapping model and source-matched QTL LD were absent.

This plan will not force that route to resolve using a convenient but
incompatible LD panel. Its primary goal is to discover whether an independent
public xQTL route can resolve `RPS15`; its secondary goal is to identify the
exact public-data boundary if none can.

## Why RPS15 is the priority

The completed endophenotype extension tested all 19 nuclear Phase 18 genes
against CSF amyloid-beta 42, total tau, and p-tau181. Only `APOE` passed the
GWAS gates, and no new gene was validated.

Under the AD-diagnosis GWAS, `RPS15` remains more valuable than further APOE
work when the objective is to add a new supported gene:

- `RPS15` has a frozen regional AD association with
  `P = 4.089e-30`;
- the primary OPC candidate is independently selected by Phase 18;
- the bulk-neocortex eQTL route has a candidate-gene signal;
- a valid shared-signal result could add a genuinely new gene; and
- APOE is already genetically established, so resolving APOE would mostly add
  mechanistic detail rather than a new validated gene.

This is still a high-risk recovery. Public xQTL releases may show a signal but
provide only PIP or credible-set summaries rather than the fitted multi-signal
model or compatible LD needed for primary colocalization. The plan therefore
defines success as a valid, terminal public-data result—not as a required
positive H4.

## Relationship to completed Phase 19 work

The following result bundles are immutable inputs:

```text
results/minerva_production/19_genetic_support/
results/minerva_production/19_genetic_support_tier2/
results/minerva_production/19_genetic_support_tier2_recovery/
results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension/
```

The authoritative existing `RPS15` rows are in:

- `recovery_regional_gwas_summary.tsv`;
- `recovery_regional_qtl_summary.tsv`; and
- `recovery_route_decisions.tsv`.

The workstream must hash and verify these inputs before inspecting any new
`RPS15` xQTL result. It must not modify or republish into an existing result
directory.

The relevant frozen recovery states are:

| Candidate/context | Existing source | Current terminal state | Reason |
|---|---|---|---|
| `GS045 RPS15 OPCs` | `QTD000579` bulk neocortex eQTL | `model_or_ld_incompatible` | Dense regional eQTL signal exists, but the released SuSiE model and source-matched QTL LD are unavailable. |
| `GS045 RPS15 OPCs` | `QTD000583` bulk neocortex sQTL | `not_assessable` | Target-gene splicing event is absent from the released conditional/model files. |
| `GS044 RPS15 Inhibitory_neurons` | `QTD000569` neuronal eQTL | `no_regional_qtl_signal` | Complete indexed region fails the frozen per-gene eQTL signal gate. |
| `GS044 RPS15 Inhibitory_neurons` | `QTD000573` neuronal sQTL | `not_assessable` | Target-gene splicing-event measurement remains unresolved. |

Existing negative and unavailable states remain valid for those exact sources.
A new source may add an independent route; it must not overwrite an unfavorable
old route.

## Authoritative filesystem layout

All paths below are absolute and are part of the execution contract.
The locations are:

```text
project_root = /home/ericzhuang2010/VscodeProjects/alzheimer
plan_file = /home/ericzhuang2010/VscodeProjects/alzheimer/docs/phase_19_genetic_support/opc_rps15/opc_rps15_public_data_first_plan.md
configuration_root = /home/ericzhuang2010/VscodeProjects/alzheimer/config
analysis_script_root = /home/ericzhuang2010/VscodeProjects/alzheimer/scripts
test_root = /home/ericzhuang2010/VscodeProjects/alzheimer/tests
existing_ng00184_input_root = /home/ericzhuang2010/VscodeProjects/alzheimer/data/reference/phase19_genetic_support/endophenotype_gwas_qtl_extension/qtl_coverage/NG00184
previous_phase19_result_root = /home/ericzhuang2010/VscodeProjects/alzheimer/results/minerva_production
new_targeted_download_root = /home/ericzhuang2010/VscodeProjects/alzheimer/data/reference/phase19_genetic_support/opc_rps15_public_recovery/targeted_downloads
compact_regional_extract_root = /home/ericzhuang2010/VscodeProjects/alzheimer/data/reference/phase19_genetic_support/opc_rps15_public_recovery/regional_extracts
temporary_work_root = /home/ericzhuang2010/VscodeProjects/alzheimer/data/reference/phase19_genetic_support/opc_rps15_public_recovery/work
staging_result_root = /home/ericzhuang2010/VscodeProjects/alzheimer/results/minerva_production/.19_genetic_support_opc_rps15_public_recovery.staging
final_result_root = /home/ericzhuang2010/VscodeProjects/alzheimer/results/minerva_production/19_genetic_support_opc_rps15_public_recovery
execution_report = /home/ericzhuang2010/VscodeProjects/alzheimer/docs/phase_19_genetic_support/opc_rps15/opc_rps15_public_data_first_execution_report.md
```

Directory ownership is fixed:

- configuration code goes only in `configuration_root`;
- analysis and validation programs go only in `analysis_script_root`;
- automated tests go only in `test_root`;
- existing NG00184 archives remain in `existing_ng00184_input_root`;
- permitted small public downloads go only in `new_targeted_download_root`;
- compact RPS15 regional extracts go only in `compact_regional_extract_root`;
- disposable intermediate files go only in `temporary_work_root`;
- the 24-file candidate result bundle is built only in `staging_result_root`;
- a successful atomic publication renames staging to `final_result_root`; and
- no code or result file may be written outside these declared locations.

The literal directory name `minerva_production` is only the repository's
local production-results namespace. It neither requires nor permits a Minerva
cluster job for this workstream.

## Frozen scientific questions

### Primary question

> In a public, context-matched molecular-QTL source, does the
> AD-associated `RPS15` region contain a significant cis-QTL for `RPS15`,
> and, if so, do compatible multi-signal fine-mapping models support a shared
> causal signal?

### Context question

> Is any shared signal present in OPCs or a defensible oligodendroglial
> lineage context, rather than only in unrelated cell types or bulk tissue?

### Independence question

> Does the supporting QTL cohort exclude ROSMAP/Rush participants used to
> produce the Phase 18 key driver, or must the result be labeled
> mechanism/triangulation evidence?

### Public-data boundary question

> If primary colocalization remains impossible, which exact public component
> is missing: measurement, a QTL signal, complete regional statistics, a
> fitted signal model, compatible LD, or independent cohort evidence?

## Frozen target and locus

The primary target is fixed before any new RPS15 xQTL query:

```text
candidate_id = GS045
gene = RPS15
ensembl_gene_id = ENSG00000115268
phase18_context = OPCs
chromosome = 19
gwas_accession = GCST90027158
gwas_trait = Alzheimer disease diagnosis
regional_min_p = 4.089e-30
primary_question = shared_multi_signal_AD_GWAS_and_RPS15_QTL
```

The inhibitory-neuron candidate `GS044` is retained as a separate secondary
context. Its evidence must not be combined with or relabeled as OPC evidence.

The primary locus coordinates must be copied from the completed recovery
bundle, including its source hash. Coordinates must not be recalculated from a
newer annotation after viewing the xQTL data.

No additional gene, locus, cell type, molecular phenotype, or p-value threshold
may be introduced after the RPS15 result is inspected. `COX7C` and
`ANKRD11` can reuse validated code later, but they are outside this plan and
require a separately frozen extension.

## Source scope frozen before RPS15 lookup

### Source A: existing EQTL Catalogue routes

Retain the four existing RPS15 routes exactly as completed. The main positive
fallback route is:

```text
dataset_id = QTD000579
study_id = QTS000034
modality = eQTL
context = neocortex
context_match = bulk_brain_fallback
sample_size = 211
regional_rows = 13,302
qtl_signal_present = true
existing_state = model_or_ld_incompatible
```

This route can be rerun only if a new, public, compatible model or LD input is
found. A generic reference panel may be used only as a labeled sensitivity and
cannot promote the route to validated.

### Source B: ADSP FunGen xQTL Atlas NG00184.v1

The following result-blind public archives have already been downloaded and
official-MD5 verified. They occupy approximately 4.0 GiB in total, so they do
not need to be downloaded again:

| Modality | HMT-significant archive | Single-context fine-mapping archive |
|---|---:|---:|
| eQTL | 1,022,935,040 bytes | 365,291,520 bytes |
| pQTL | 33,095,680 bytes | 30,515,200 bytes |
| sQTL | 862,525,440 bytes | 563,374,080 bytes |
| Single-nucleus eQTL | 1,005,946,880 bytes | 313,733,120 bytes |

The archive manifests register 280 chromosome 19 members totaling about
200.6 MiB compressed across the eight releases. Those members must be streamed
from the existing tar files one at a time; the archives must not be completely
extracted. The `RPS15` target rows have not been used to design this plan.
Source selection, context matching, thresholds, and stopping rules must be
frozen before the first RPS15-specific query.

The official metadata fields—not filename abbreviations alone—must define:

- cohort;
- cell type;
- biosample type;
- tissue category;
- assay;
- genome build;
- release component; and
- source overlap.

Cohorts must remain separate. A favorable result in one cohort cannot be
merged with another cohort to manufacture replication.

### Source C: small public regional extracts only

Full `all` archives are registered for provenance but prohibited as local
acquisitions in this workstream. This prohibition applies even if a transient
free-space check suggests that one archive might fit. Preserving working disk
space takes priority over acquiring a whole modality for one gene.

The inventory sizes are approximately:

| Modality | Full archive size | Decision in this plan |
|---|---:|---|
| eQTL | 468.9 GB | Prohibited. |
| Single-nucleus eQTL | 251.4 GB | Prohibited. |
| sQTL | 101.4 GB | Prohibited. |
| pQTL | 22.0 GB | Prohibited; any future exception requires a separate explicit plan amendment. |

A small public extract may be acquired only when all of these gates pass:

1. the already-local HMT/fine-mapping release establishes a signal-positive
   eligible RPS15 route that needs more statistics;
2. the public object is explicitly limited to the target, frozen locus,
   chromosome 19, or one registered context;
3. it contains the beta, standard error, alleles, frequency, sample size, and
   variant coverage needed by the intended method;
4. its verified compressed size is no larger than 5 GiB;
5. cumulative new source data for this workstream remain no larger than
   10 GiB; and
6. at least 50 GiB of local free space will remain after download, temporary
   processing, and output creation.

The executable storage policy is:

```text
automatic_full_archive_download = false
initial_new_download_limit_gib = 0
maximum_targeted_download_gib = 5
maximum_total_new_download_gib = 10
minimum_free_disk_after_processing_gib = 50
full_eqtl_archive = prohibited
full_snuc_eqtl_archive = prohibited
full_sqtl_archive = prohibited
full_pqtl_archive = prohibited
```

If a usable public source exists only as an oversized full archive, the route
ends as `oversized_public_archive_only`. If a nominally targeted file fails a
size, cumulative-download, or free-space gate, it ends as
`not_assessable_local_resource_gate`. Neither state may trigger an unplanned
Minerva migration, deletion of other data, or full-archive streaming over the
network.

### Optional author outreach

An optional request may ask for aggregate, deidentified derived data such as:

- a candidate-region LD matrix;
- a fitted SuSiE/fSuSiE object;
- variant-by-signal alpha or log-Bayes-factor matrices;
- complete regional summary statistics; or
- an author-run candidate-specific colocalization.

The request is not part of the critical path. Every output and status must be
complete if no request is sent or no reply is received. The only allowed
request states are:

```text
not_sent_optional
sent_optional_no_dependency
public_response_received_and_validated
public_response_received_incompatible
```

There is no `waiting_for_author` state.

## Context-matching hierarchy

The primary OPC route hierarchy is frozen as follows:

1. exact OPC single-nucleus eQTL;
2. exact OPC sQTL, if explicitly measured;
3. prespecified oligodendroglial-lineage eQTL or sQTL;
4. bulk adult brain eQTL or sQTL, labeled fallback;
5. brain or CSF cis-pQTL, labeled protein-level rather than OPC-specific.

The inhibitory-neuron route hierarchy is separate:

1. exact inhibitory-neuron single-nucleus eQTL;
2. exact inhibitory-neuron sQTL;
3. prespecified neuronal-lineage QTL;
4. bulk adult brain fallback.

Astrocyte, microglial, monocyte, excitatory-neuron, or unrelated peripheral
signals must not be labeled OPC or inhibitory-neuron evidence. They may be
retained in a source audit with `context_not_eligible`, but they cannot
contribute to the candidate grade.

Bulk tissue can support RPS15 at the gene level if colocalization is valid. It
cannot validate the Phase 18 OPC context.

## Measurement and QTL-signal rules

HMT-significant files are significant-only tables. Absence of RPS15 from an HMT
file alone must never be called “no QTL signal.”

A route may be called measured with no source-significant QTL only when one of
these conditions holds:

- the fine-mapping record explicitly identifies `RPS15` and states
  `is_hmt_signif=false`;
- a complete all-association file demonstrates target measurement and fails the
  frozen source threshold; or
- official metadata provides an explicit target-measurement inventory plus a
  valid source-level null result.

Route states are:

| State | Required evidence |
|---|---|
| `qtl_context_not_measured` | Official inventory establishes that RPS15 or the molecular event was not measured. |
| `measurement_unresolved` | Significant-only absence without independent measurement evidence. |
| `no_regional_qtl_signal` | RPS15 was measured, regional coverage is valid, and the source-declared signal gate fails. |
| `qtl_signal_present` | A source-declared significant cis-QTL exists in an eligible context. |
| `model_or_ld_incompatible` | GWAS and QTL signals exist, but complete compatible multi-signal inputs do not. |
| `resolved_public_colocalization` | Primary shared/distinct-signal analysis passes all model and LD gates. |

A fine-mapping PIP, a credible-set label, a lead-variant match, or physical
overlap is not H4 and must not be converted into a shared-signal conclusion.

## Build, variant, and allele contract

The existing AD GWAS and NG00184 xQTL sources do not necessarily use the same
genome build. Every route must record:

- source build;
- coordinate convention;
- reference genome;
- variant identifier;
- reference and alternate alleles;
- effect allele;
- other allele;
- beta and standard error;
- allele frequency;
- sample size; and
- lift-over or normalization provenance.

GRCh37 and GRCh38 positions must never be joined directly. Preferred matching
order is:

1. normalized biallelic variant identity after validated build conversion;
2. rsID plus allele confirmation; and
3. position plus exact reference/alternate allele confirmation.

Lift-over requires reference-allele validation against the destination genome.
Multiallelic, duplicate, mismatched, and ambiguous palindromic variants must
have explicit exclusion reasons. Allele swaps must reverse beta signs.

## Public-only model and LD decision tree

For every eligible source/context route:

1. **No verified measurement:** terminate as
   `qtl_context_not_measured` or `measurement_unresolved`.
2. **Measured but no qualifying QTL:** terminate as
   `no_regional_qtl_signal`.
3. **QTL signal plus complete released fitted model:** validate model schema,
   variant order, signal count, and build, then proceed.
4. **QTL signal plus complete regional statistics and compatible public LD:**
   fine-map locally one locus at a time, then proceed.
5. **QTL signal plus only PIP/credible-set summaries:** terminate primary
   analysis as `model_or_ld_incompatible`; retain overlap summaries as
   non-graded descriptive evidence.
6. **Complete statistics plus generic 1000 Genomes EUR LD only:** permit
   single-signal or reference-LD sensitivity, but no strong/moderate
   validation.
7. **No compatible public model or LD:** close the route. Do not wait for
   authors.

A public LD panel is compatible only after passing:

- ancestry compatibility;
- genome-build compatibility;
- identical normalized alleles;
- exact common-variant order;
- unit diagonal;
- symmetry and finiteness;
- acceptable minimum eigenvalue;
- sufficient variant retention;
- summary/LD consistency; and
- sensitivity to reference-panel choice.

## Primary analysis

### GWAS model

Reuse the frozen AD-diagnosis GWAS locus and its completed regional signal
gate. Do not reselect the lead variant, widen the locus, or change the threshold
after viewing QTL data.

If a new public LD panel is used, rerun the GWAS fine-mapping under that exact
variant space. Record whether it is source-matched or a reference-panel
sensitivity.

### QTL model

The primary QTL analysis requires either:

- a complete released multi-signal model; or
- complete regional beta/SE/allele/frequency/sample-size statistics plus
  compatible LD permitting local SuSiE/fSuSiE fine-mapping.

Fine-map each cohort and context independently. Do not pool cohorts after
viewing which one is favorable.

### Colocalization

Use `coloc.susie` or equivalent signal-aware Bayes-factor comparison only
after both models pass QC. Retain every GWAS-signal/QTL-signal pair and report:

```text
PP.H0
PP.H1
PP.H2
PP.H3
PP.H4
PP.H4 / (PP.H3 + PP.H4)
GWAS signal ID
QTL signal ID
credible sets
warnings
```

Frozen priors and thresholds are:

```text
p1 = 1e-4
p2 = 1e-4
primary_p12 = 5e-6
p12_sensitivity = 1e-6, 5e-6, 1e-5
robust_shared_signal = PP.H4 >= 0.80
conditional_shared_signal =
  PP.H4 / (PP.H3 + PP.H4) >= 0.80
suggestive_shared_signal = 0.50 <= PP.H4 < 0.80
distinct_signals = PP.H3 > PP.H4 with adequate model QC
```

`coloc.abf`, SMR/HEIDI, lead-variant concordance, and credible-set overlap may
be retained as sensitivity or screening results. They cannot replace the
multi-signal primary analysis or independently validate RPS15.

## Sample-overlap and independence audit

For each cohort, explicitly audit:

- Phase 18 ROSMAP discovery versus QTL cohort;
- Bellenguez AD GWAS versus QTL cohort;
- overlap among QTL cohorts; and
- whether leave-ROSMAP-out or non-ROSMAP results exist.

Interpretation classes are:

| Overlap state | Permitted interpretation |
|---|---|
| Independent QTL cohort with no known discovery overlap | Independent gene-level validation eligible. |
| Exact OPC result with ROSMAP overlap | OPC mechanism/triangulation evidence; not fully independent validation. |
| Bulk brain result with no ROSMAP overlap | Independent gene-level evidence; no OPC-context validation. |
| Bulk brain result with ROSMAP overlap | Gene-level mechanism evidence only. |
| Overlap unresolved | Qualified support only; no unqualified independence claim. |

A favorable ROSMAP-derived result is scientifically useful but cannot be
counted as an independent replication of a ROSMAP-derived key driver.

## Evidence grades and the meaning of validation

This plan distinguishes gene-level and context-level support.

### Strong new RPS15 validation

Requires all of:

- a valid source-significant RPS15 QTL;
- complete compatible multi-signal GWAS and QTL models;
- robust shared-signal thresholds;
- adequate harmonization and LD QC;
- an independent or leave-ROSMAP-out QTL cohort; and
- no contradictory stronger signal-pair result.

An exact OPC result permits strong OPC-context support. A bulk result can
support the gene but cannot validate the OPC context.

### Moderate RPS15 support

Permitted when robust shared-signal evidence passes but one limitation remains,
such as:

- ROSMAP participant overlap;
- defensible oligodendroglial-lineage rather than exact OPC context; or
- bulk-brain fallback.

The limitation must be in the grade label and conclusion text.

### Weak or suggestive support

Includes:

- corrected TWAS/PWAS;
- SMR/HEIDI;
- single-signal `coloc.abf`;
- PIP/credible-set overlap;
- lead-variant concordance; or
- a source-significant QTL without compatible shared-signal models.

These results guide follow-up but do not count as a newly validated gene.

### No support versus not assessable

`no_regional_qtl_signal` is evidence against the tested molecular mechanism
in that measured context. `model_or_ld_incompatible` is an unresolved
technical limitation, not negative biological evidence. Neither may be
rewritten as the other.

## Public TWAS/PWAS/SMR fallback

If every classical-colocalization route ends without compatible public model
or LD inputs, run only preregistered public prediction models or summary-based
screening methods with valid coverage.

The fallback must:

1. freeze brain and OPC/oligodendroglial model sources before RPS15 results;
2. include all valid models from each registered source;
3. correct the complete registered model family;
4. report neighboring correlated genes and model competition;
5. retain null and discordant models; and
6. grade a positive result as weak/suggestive unless independently supported.

The fallback is worthwhile as a prioritization screen. It is not a substitute
for classical colocalization and cannot by itself produce strong or moderate
validation.

If no suitable public weights exist, emit a terminal
`prediction_model_not_available` row rather than searching indefinitely.

## Out-of-scope routes

The following are not part of this local public-data plan:

- controlled individual-level QTL genotypes;
- waiting for investigator data;
- custom cloud or Minerva migration;
- downloading any full `all` archive, including the 468.9-GB eQTL,
  251.4-GB single-nucleus eQTL, 101.4-GB sQTL, and 22.0-GB pQTL archives;
- rare-variant burden/SKAT-O;
- experimental perturbation;
- adding COX7C, ANKRD11, APOE, or another gene after RPS15 results;
- sex/APOE interaction GWAS; and
- mtDNA association.

If the public RPS15 route remains unresolved, rare-variant burden analysis of
all 19 nuclear candidates is the recommended separate controlled-data
workstream. It requires its own access, ancestry, variant-mask, compute, and
replication plan.

## Local execution contract

The workstream runs locally with:

```text
execution_stage = local_production_equivalent
execution_backend = direct
project_root = /home/ericzhuang2010/VscodeProjects/alzheimer
existing_source_root = /home/ericzhuang2010/VscodeProjects/alzheimer/data/reference/phase19_genetic_support/endophenotype_gwas_qtl_extension/qtl_coverage/NG00184
targeted_data_root = /home/ericzhuang2010/VscodeProjects/alzheimer/data/reference/phase19_genetic_support/opc_rps15_public_recovery
working_root = /home/ericzhuang2010/VscodeProjects/alzheimer/data/reference/phase19_genetic_support/opc_rps15_public_recovery/work
staging_result_root = /home/ericzhuang2010/VscodeProjects/alzheimer/results/minerva_production/.19_genetic_support_opc_rps15_public_recovery.staging
final_result_root = /home/ericzhuang2010/VscodeProjects/alzheimer/results/minerva_production/19_genetic_support_opc_rps15_public_recovery
publication_namespace = minerva_production
use_minerva = false
gpu_required = false
max_download_workers = 1
automatic_full_archive_download = false
initial_new_download_limit_gib = 0
maximum_targeted_download_gib = 5
maximum_total_new_download_gib = 10
maximum_working_directory_gib = 10
maximum_staging_result_gib = 1
maximum_total_new_disk_footprint_gib = 20
minimum_free_disk_after_processing_gib = 50
allow_full_all_archives = false
stream_existing_archive_members = true
max_analysis_workers = 1
process_one_locus_at_a_time = true
physical_memory_gib = 15
reserve_memory_gib = 6
hard_memory_limit_per_locus_gib = 9
minimum_free_disk_gib = 50
deterministic_gzip_mtime = 0
```

All large source files remain outside the final publication directory. The
final bundle contains only compact evidence, provenance, QC, figures, hashes,
and status tables.

Credentials, tokens, cookies, signed URLs, and authorization headers must not
appear in commands captured in reports or in any repository/result artifact.

## Planned implementation files

Every path below is relative to the absolute `project_root` declared above.
These are the only code, test, and execution-report files this plan will add.

```text
config/phase19_opc_rps15_public_recovery.yml
config/phase19_opc_rps15_local_execution.yml
scripts/19_audit_opc_rps15_public_qtl.py
scripts/19_extract_opc_rps15_public_qtl.py
scripts/19_prepare_opc_rps15_ld.py
scripts/19_run_opc_rps15_finemapping.R
scripts/19_run_opc_rps15_coloc.R
scripts/19_integrate_opc_rps15_evidence.py
scripts/19_validate_opc_rps15_public_recovery.py
tests/test_phase19_opc_rps15_public_recovery.py
tests/test_phase19_opc_rps15_public_recovery.R
docs/phase_19_genetic_support/opc_rps15/
  opc_rps15_public_data_first_execution_report.md
```

Shared Phase 19 harmonization, LD-QC, multi-signal pilot, artifact hashing, and
status-precedence functions should be reused where their contracts match.
Shared dispatch code may register a new task but must not change defaults of a
completed Phase 19 phase.

## Detailed execution tasks

### Task 0: freeze and hash the handoff

1. Hash all four completed Phase 19 bundles.
2. Copy the exact `GS045` and `GS044` candidate rows.
3. Copy the frozen RPS15 locus and AD GWAS signal row.
4. Freeze the source/context hierarchy and thresholds in configuration.
5. Write a result-blind route manifest.
6. Record that author data are optional and non-blocking.
7. Hash the freeze before querying RPS15 in NG00184.

Deliverable: immutable baseline and pre-result route manifests.

### Task 1: validate existing public files

1. Recompute official MD5 for all eight NG00184 archives plus metadata.
2. Recompute local SHA-256.
3. verify file sizes and release version;
4. verify chromosome 19 archive-member coverage without completely extracting
   any tar file;
5. map every file to official cohort/cell/tissue metadata; and
6. confirm no RPS15-specific query occurred before the freeze.

Deliverable: public source inventory and checks.

### Task 2: run the result-blind RPS15 measurement/signal audit

1. Query `ENSG00000115268` and symbol `RPS15`.
2. retain every matching target/event/protein separately;
3. distinguish exact OPC, lineage, inhibitory, bulk, and ineligible contexts;
4. distinguish HMT-significant and fine-mapping components;
5. record source `is_hmt_signif`, PIP, credible-set fields, and underlying
   p-value/FDR metadata;
6. never infer a null result from HMT absence alone; and
7. assign measurement and signal states per cohort/context/modality.

Deliverable: complete RPS15 public-QTL audit without H4 selection.

### Task 3: apply public-data acquisition gates

For each signal-positive eligible route:

1. inventory small target/locus/chromosome/context extracts and register full
   archive availability for provenance only;
2. validate required beta/SE/allele/frequency/sample-size fields;
3. perform no new download during the initial already-local audit;
4. reject every full `all` archive, including pQTL and sQTL;
5. allow only a complete targeted file no larger than 5 GiB while keeping
   cumulative new source data no larger than 10 GiB;
6. verify that at least 50 GiB will remain after download and temporary work;
7. stream one existing chromosome 19 archive member at a time; and
8. assign a terminal resource/source state when acquisition is invalid.

Deliverable: immutable public acquisition decisions and checksums.

### Task 4: harmonize candidate-region statistics

1. normalize builds and variants;
2. validate lift-over and destination reference alleles;
3. create exact common variant sets;
4. flip swapped effect signs;
5. exclude ambiguous or mismatched variants with reasons;
6. verify regional coverage and finite beta/SE fractions; and
7. stop sparse or filtered regions before fine-mapping.

Deliverable: harmonized summary statistics plus a full exclusion audit.

### Task 5: validate public LD or fitted models

1. prefer source-released fitted QTL models;
2. otherwise validate a public source/ancestry-compatible LD panel;
3. align LD to the exact common variant order;
4. run matrix and summary/LD QC;
5. label generic EUR reference LD as sensitivity only; and
6. terminate primary analysis if no compatible public model/LD exists.

Deliverable: model/LD QC or exact `model_or_ld_incompatible` state.

### Task 6: fine-map and colocalize resolved routes

1. fine-map GWAS and QTL independently;
2. retain all converged signals and credible sets;
3. run all signal pairs with frozen priors;
4. retain H0-H4 and conditional H4;
5. run prior and locus-boundary sensitivities;
6. retain distinct or conflicting signals; and
7. grade only after model, LD, overlap, and context QC.

Deliverable: primary and sensitivity colocalization tables. Header-only primary
tables are valid when no public route passes the model/LD gate.

### Task 7: run non-primary public fallback analyses

1. inventory registered TWAS/PWAS/SMR models;
2. run all valid registered models;
3. correct the full testing family;
4. perform neighboring-gene/model competition where possible;
5. retain negative and conflicting models; and
6. cap evidence at weak/suggestive.

Deliverable: complete fallback table or explicit model-unavailable state.

### Task 8: integrate gene and context conclusions

1. preserve old route results;
2. add every new public route as a separate row;
3. calculate gene-level and OPC-context grades separately;
4. apply independence limitations;
5. do not count repeated contexts as independent replications;
6. generate conclusion wording from structured states; and
7. report whether RPS15 is newly supported, still unresolved, or unsupported
   in each tested context.

Deliverable: RPS15 evidence summary and context-specific matrix.

### Task 9: validate and publish atomically

1. write only to `staging_result_root` and refuse to overwrite either the
   staging or final result directory;
2. validate all schemas, hashes, row counts, and terminal states;
3. recompute grades from detailed evidence;
4. run output-only validation in a clean process;
5. scan for credentials and signed URLs;
6. verify no prior Phase 19 mutation;
7. require no undeclared files; and
8. rename `staging_result_root` to `final_result_root` only after every blocking check passes.

Deliverable: validated local production bundle.

### Task 10: write the execution report

Record:

- exact local commands and versions;
- source files, bytes, official MD5, and SHA-256;
- frozen route and context definitions;
- measurement, signal, model, and LD states;
- all primary and sensitivity results;
- sample overlap and independence limits;
- optional outreach state without dependency;
- whether RPS15 gained gene-level or OPC-context support; and
- the next controlled-data action if public routes remain unresolved.

## Planned output contract

The exact final directory is
`/home/ericzhuang2010/VscodeProjects/alzheimer/results/minerva_production/19_genetic_support_opc_rps15_public_recovery/`.
It must contain exactly these 24 files and no others:

```text
opc_rps15_analysis_manifest.tsv
opc_rps15_frozen_scope.tsv
opc_rps15_route_manifest.tsv
opc_rps15_dataset_registry.tsv
opc_rps15_request_manifest.tsv
opc_rps15_input_inventory.tsv
opc_rps15_source_checks.tsv
opc_rps15_qtl_audit.tsv
opc_rps15_acquisition_decisions.tsv
opc_rps15_variant_harmonization.tsv.gz
opc_rps15_variant_harmonization_summary.tsv
opc_rps15_ld_qc.tsv
opc_rps15_gwas_finemapping.tsv.gz
opc_rps15_qtl_finemapping.tsv.gz
opc_rps15_colocalization.tsv.gz
opc_rps15_colocalization_qc.tsv
opc_rps15_prior_sensitivity.tsv.gz
opc_rps15_twas_pwas_smr.tsv
opc_rps15_sample_overlap_audit.tsv
opc_rps15_assessability.tsv
opc_rps15_evidence_summary.tsv
opc_rps15_checks.tsv
opc_rps15_artifacts.tsv
opc_rps15_status.tsv
```

Conditional or primary-analysis tables must exist with valid headers even if no
route passes the model/LD gate. Raw archives, extracted chromosome files,
indexes, caches, credentials, and temporary files are forbidden in the final
directory.

## Required automated tests

### Freeze and provenance

- exact `GS045` and `GS044` handoff;
- exact `ENSG00000115268` identity;
- exact frozen locus and AD GWAS row;
- unchanged hashes for all completed bundles;
- official NG00184 MD5 and local SHA-256;
- route/source selection frozen before RPS15 lookup; and
- optional author request never blocks completion.

### Storage safety

- the initial audit downloads zero new source bytes;
- chromosome 19 members are streamed without complete tar extraction;
- every full `all` archive is rejected, including pQTL and sQTL;
- a targeted file larger than 5 GiB is rejected;
- cumulative new source data larger than 10 GiB are rejected;
- processing that would leave less than 50 GiB free is rejected;
- a working directory larger than 10 GiB is rejected;
- a staging result larger than 1 GiB is rejected;
- total new disk use larger than 20 GiB is rejected;
- any code or result path outside the authoritative layout is rejected; and
- an oversized-only source receives a terminal route state.

### Measurement and context

- HMT absence alone produces `measurement_unresolved`, not no signal;
- explicit `is_hmt_signif=false` supports measured/no-source-signal;
- exact OPC, oligodendroglial lineage, inhibitory, bulk, and ineligible context
  states remain distinct;
- microglia/monocyte signals cannot support OPC;
- cohort-specific routes are not pooled; and
- gene, event, and protein identifiers map unambiguously.

### Harmonization and build

- GRCh37/GRCh38 positions are never directly joined;
- successful and failed lift-over;
- reference-allele validation;
- match, swap, complement, and swap-complement;
- beta sign reversal;
- multiallelic and duplicate handling;
- palindromic exclusion; and
- sparse/incomplete region rejection.

### LD, fine-mapping, and colocalization

- LD order, symmetry, diagonal, finiteness, PSD, and ancestry;
- summary/LD mismatch rejection;
- shared and distinct multi-signal fixtures;
- nonconvergence handling;
- all signal pairs retained;
- H0-H4 and conditional-H4 arithmetic;
- all three `p12` values;
- PIP/credible-set overlap never becomes H4;
- reference-LD or single-signal result cannot produce strong/moderate support;
  and
- missing public model/LD produces a terminal state without author waiting.

### Integration and publication

- strong/moderate/weak/no-support/not-assessable precedence;
- gene-level and OPC-context grades remain separate;
- ROSMAP overlap restricts independence wording;
- repeated contexts do not count as replication;
- exact 24-file contract;
- header-only conditional tables validate;
- every route has exactly one terminal state;
- artifact hashes reproduce;
- execution backend is `direct`;
- no prior bundle mutation; and
- no token-like or signed-URL text.

## Blocking gates

Publication is forbidden if:

- the candidate, locus, source hierarchy, or thresholds changed after RPS15
  lookup;
- an old Phase 19 bundle changed;
- a full `all` archive download or network stream is attempted;
- an existing tar archive is completely extracted;
- a targeted public file exceeds 5 GiB;
- cumulative new source data exceed 10 GiB;
- the working directory exceeds 10 GiB;
- staging results exceed 1 GiB;
- total new disk use exceeds 20 GiB;
- code or results are written outside the authoritative filesystem layout;
- projected free disk after processing is below 50 GiB;
- RPS15 measurement is inferred from significant-only absence;
- an ineligible cell type is promoted to OPC;
- a bulk route is labeled OPC-specific;
- builds or alleles are unresolved;
- incomplete fine-mapping rows are treated as full regional statistics;
- PIP or credible-set overlap is reported as H4;
- generic reference LD is promoted to a primary source-matched result;
- an author response is required to finish;
- a route lacks a terminal state;
- overlap limitations are hidden;
- a strong/moderate grade cannot be regenerated;
- a required output is missing or undeclared; or
- a credential appears in any artifact.

An unavailable public input does not block the whole workstream. It closes only
the affected route with a precise terminal reason.

## Completion criteria

Technical completion requires:

```text
validation_status = validated_complete_opc_rps15_public_recovery
candidate_gene = RPS15
primary_candidate_id = GS045
secondary_candidate_id = GS044
author_data_required = false
automatic_full_archive_download = false
full_archive_download_count = 0
maximum_targeted_download_gib = 5
maximum_total_new_download_gib = 10
maximum_working_directory_gib = 10
maximum_staging_result_gib = 1
maximum_total_new_disk_footprint_gib = 20
authoritative_path_contract_valid = true
all_registered_routes_terminal = true
baseline_phase19_hashes_unchanged = true
declared_output_files = 24
undeclared_output_files = 0
blocking_check_failures = 0
execution_backend = direct
```

Scientific completion permits any of these final outcomes:

```text
new_independent_RPS15_gene_validation
new_RPS15_gene_support_with_context_or_overlap_limitation
suggestive_public_support_only
assessable_no_RPS15_QTL_signal
public_model_or_ld_incompatible
public_measurement_unresolved
oversized_public_archive_only
```

The workstream is complete even if RPS15 remains unresolved. Completion means
that every frozen public route has been tested as far as valid public data
permit, no favorable but invalid substitute was used, and no task remains
waiting for an author.

## Recommended execution order

1. Freeze and hash the RPS15 handoff.
2. Freeze public source/context routes and optional-outreach policy.
3. Revalidate existing files and official metadata.
4. Query RPS15 measurement and signal states result-blind.
5. For signal-positive routes, seek only complete targeted public extracts and
   reject every full archive.
6. Harmonize complete eligible regional statistics.
7. Validate public fitted models or LD.
8. Fine-map and colocalize only compatible routes.
9. Run preregistered weak-evidence fallback models.
10. Integrate gene-level and OPC-context conclusions.
11. Validate and atomically publish the 24-file bundle.
12. Write the report and, if unresolved, hand off to a separately planned
    controlled-data rare-variant workstream.

## Acceptance checklist before execution

- [ ] `GS045`, `GS044`, RPS15 identity, and locus match frozen outputs.
- [ ] All prior Phase 19 bundle hashes are captured.
- [ ] NG00184 archive and metadata hashes are verified.
- [ ] No RPS15-specific NG00184 result has been used to select sources,
  contexts, thresholds, or methods.
- [ ] OPC, oligodendroglial, inhibitory, bulk, and ineligible context rules are
  configured.
- [ ] HMT absence cannot be interpreted as no signal.
- [ ] The initial audit downloads no new source data.
- [ ] Every full `all` archive is prohibited.
- [ ] Targeted-file and cumulative-download ceilings are 5 GiB and 10 GiB.
- [ ] At least 50 GiB must remain free after processing.
- [ ] All code, input, work, staging, report, and final paths match the authoritative layout.
- [ ] Work, staging, and total-new-disk caps are 10 GiB, 1 GiB, and 20 GiB.
- [ ] Existing staging or final result directories cause a no-overwrite stop.
- [ ] Existing chromosome 19 members are streamed without full extraction.
- [ ] Author outreach is optional and has no waiting state.
- [ ] Generic reference LD is sensitivity-only.
- [ ] PIP/credible-set overlap cannot become H4.
- [ ] Primary multi-signal thresholds are frozen.
- [ ] ROSMAP overlap restricts independence claims.
- [ ] Public TWAS/PWAS/SMR cannot exceed weak evidence alone.
- [ ] The validator enforces the exact 24-file contract.
- [ ] Reporting distinguishes RPS15 gene support from OPC-context validation.
