# Phase 19 Tier 1: Human Genetic Support for Phase 18 Key Drivers

## Status and phase boundary

This document is the scientific, implementation, data-acquisition, execution,
output, and completion plan for Phase 19 Tier 1. The cross-workstream status and
future priorities are maintained in the [Phase 19 overall roadmap](../overall_plan.md).

Tier 1 status (2026-08-16): **implemented and validated locally** for all 25
genes and 47 candidate-context units. See the
[Tier 1 execution report](tier1_execution_report.md) and the validated bundle
in `results/minerva_production/19_genetic_support_tier1/`.

Tier 2 execution status (2026-08-21): **open-data alternative executed and
validated locally**. The canonical 23-file bundle is in
`results/minerva_production/19_genetic_support_tier2_regional/`. The original
exact-source FunGen-xQTL Synapse release is
not readable by the current account, so it is retained as a later sensitivity
route rather than a production prerequisite. The primary route uses immutable
public NIAGADS, GWAS Catalog, and ancestry-matched LD releases and preserves an
explicit `not_assessable` state wherever those releases do not support a valid
classical colocalization. All 54 routes are terminal and technically valid,
but none has classical H0-H4; this is not negative evidence. The separate
[Tier 2 regional GWAS/QTL plan](../tier2/tier2_regional_gwas_qtl_plan.md) defines that
increment, and its [execution report](../tier2/tier2_execution_report.md) records the
execution outcome. Tier 1 remains an immutable completed bundle.

Phase 19 promotes WP5 from the
[Phase 18 cross-validation guide](../../analysis/kda_phase_18/phase18_key_driver_cross_validation_guide.md)
into a standalone, reproducible phase. It asks:

> Is inherited human genetic variation associated with Alzheimer disease (AD)
> or a prespecified AD-related phenotype, and is there credible evidence that
> connects that variation to a Phase 18 key-driver candidate?

Phase 19 depends on the frozen Phase 18 key-driver selection. It reads Phase
18 results but does not rerun KDA, change the selected drivers, or modify any
Phase 18 artifact.

The scientific scope is all 25 Phase 18 genes in every corresponding displayed
broad-network context: 47 candidate-context units in total. A local pilot may
exercise synthetic or reduced-size external inputs, but it must still build
and validate the full 47-row candidate manifest. There is no seven-gene
scientific stage and no optional later expansion.

### Output roots

```text
results/local_pilot/19_genetic_support/
results/minerva_production/19_genetic_support_tier1/
```

Pilot files are nonfinal. They must not be copied into, combined with, or
promoted in place to the production directory.

The `minerva_production` directory is the repository's existing canonical
namespace for final validated results; it does not require that the computation
physically run on Minerva. A local production-equivalent run may publish there
only when the status and analysis manifest record
`execution_stage = local_production_equivalent`, `execution_backend = direct`,
and the actual hardware/resource audit. A Minerva run records
`execution_stage = minerva_production` instead.

### Execution location decision

The default Phase 19 execution is **local production-equivalent**. The
summary-level Tier 1 workflow does not need Minerva.

The local hardware audited on 2026-08-16 is:

```text
machine: Apple M4 Pro MacBook Pro
logical cores: 14
physical memory: 24 GB
available project-volume space: approximately 133 GiB
```

Use a conservative local profile:

```text
maximum analysis workers: 4
custom colocalization workers: 1
memory reserved for OS/other processes: 6 GiB
maximum estimated Phase 19 peak RAM: 16 GiB
minimum disk space left free after staging and scratch: 50 GiB
```

Run Minerva instead when any of the following is true after source inventory:

- the estimated local working set would leave less than 50 GiB free;
- an LD matrix/model is expected to push peak RAM above 16 GiB;
- several dense custom colocalizations must run concurrently;
- a full LD/reference container is required instead of small locus-specific
  inputs;
- controlled-access terms require an approved server environment; or
- the one-locus-at-a-time local run fails the same resource check twice.

Changing execution location must not change candidates, sources, priors,
methods, grades, or output schemas. It changes only the execution profile and
recorded provenance.

## The scientific question in plain language

Phase 18 identified genes that sit in influential positions in AD-associated
expression networks. That makes them plausible network drivers, but it does
not show that inherited DNA variation affects AD through those genes.

Phase 19 looks for an independent line of evidence in human genetics. In
plain language, it asks three questions:

1. Is there an AD-associated DNA signal near or within the candidate gene?
2. Can fine mapping or a molecular QTL connect that signal to the candidate,
   rather than merely to the nearest gene?
3. Is there rare-variant evidence that changes in the candidate gene are
   associated with AD?

The strongest useful result is not simply “an AD SNP is close to this gene.”
It is a chain such as:

```text
AD-associated variant
        |
        v
fine-mapped signal shared with a brain-cell eQTL or sQTL
        |
        v
the same candidate gene in a matching Phase 18 cell context
```

A negative Phase 19 result does not invalidate a Phase 18 network driver. A
gene can influence a disease-related network without common inherited
variation at its own locus measurably changing AD risk.

## What Phase 19 will and will not do

### Phase 19 will

1. freeze the Phase 18 displayed candidate-context set before examining
   external genetic evidence;
2. resolve approved symbols, stable Ensembl IDs, and GRCh38 loci;
3. register exact external sources, versions, access dates, sizes, and
   checksums;
4. screen AD GWAS loci and fine-mapping results once per gene;
5. evaluate eQTL and sQTL colocalization separately for each candidate and
   Phase 18 broad-network context;
6. use precomputed FunGen-AD results as the primary route;
7. run a custom colocalization only when the required regional statistics and
   ancestry-matched LD make that comparison assessable;
8. review published or approved summary-level rare-variant association
   results;
9. use a separate evidence track for mitochondrial-DNA genes;
10. distinguish positive, negative, ambiguous, and unassessable evidence; and
11. publish all terminal results with provenance and reproducible wording.

### Phase 19 will not

- call a candidate an AD gene solely because it is nearest to a GWAS variant;
- equate a credible set of variants with a credible set of genes;
- treat TWAS alone as proof of colocalization or causality;
- select a favorable phenotype, tissue, prior, locus window, or QTL after
  viewing candidate results;
- label absent or incomplete data as evidence of no association;
- count correlated tissues or overlapping GWAS cohorts as independent
  replication;
- infer mediation or therapeutic direction from colocalization alone;
- run a new individual-level ADSP WES/WGS burden study;
- place controlled-access participant data in this repository; or
- change Phase 18 rankings, evidence tiers, or KDA conclusions.

## Frozen scope

### Authoritative Phase 18 input

The candidate set is derived from:

```text
results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv
```

The input currently has:

```text
schema source: config/phase18_key_driver_selection.yml
selection rule: top5_display == TRUE
unique key: key_driver + broad_network + case_id
displayed candidate-context units: 47
unique genes: 25
nuclear candidate-context units: 27
mitochondrial-DNA candidate-context units: 20
nuclear genes: 19
mitochondrial-DNA genes: 6
```

The current frozen identities are:

| File | Bytes | SHA-256 |
|---|---:|---|
| `call_key_driver_returns.tsv` | 63,161,765 | `b917f70e6edcdf030f63e88ba8fbc5b22b80714599c12c80ea449e8c38bd51d8` |
| `config/phase18_key_driver_selection.yml` | 2,437 | `d1979ef4b66d1e841633a2f235419147fa130da140d20b40c2d84b99cd90ae4f` |

The implementation must stop if either hash differs, the selection rule does
not produce exactly 47 unique units and 25 unique genes, or a key is
duplicated. A scientifically intentional upstream change requires a new Phase
19 analysis version and updated expected counts; it must not be absorbed
silently.

### Full 25-gene scope

All of the following genes and Phase 18 broad-network contexts belong to the
primary production analysis:

| Gene | Phase 18 broad-network context(s) | Context units |
|---|---|---:|
| `ANKRD11` | `OPCs` | 1 |
| `APOE` | `Astrocytes` | 1 |
| `ATP6V1F` | `Inhibitory_neurons` | 1 |
| `COX4I1` | `Astrocytes`; `Excitatory_neurons` | 2 |
| `COX6B1` | `Excitatory_neurons` | 1 |
| `COX7C` | `Astrocytes`; `Inhibitory_neurons` | 2 |
| `DYNLT1` | `Excitatory_neurons` | 1 |
| `FTL` | `OPCs` | 1 |
| `LAMTOR5` | `Excitatory_neurons`; `Inhibitory_neurons` | 2 |
| `LAPTM4A` | `Astrocytes` | 1 |
| `MT-ATP6` | `Astrocytes`; `Vasculature_cells` | 2 |
| `MT-CO2` | `Astrocytes`; `Excitatory_neurons`; `Inhibitory_neurons`; `Microglia`; `OPCs`; `Oligodendrocytes`; `Vasculature_cells` | 7 |
| `MT-CO3` | `Astrocytes`; `Inhibitory_neurons`; `OPCs`; `Vasculature_cells` | 4 |
| `MT-CYB` | `Excitatory_neurons`; `Inhibitory_neurons` | 2 |
| `MT-ND4` | `Microglia`; `OPCs`; `Oligodendrocytes`; `Vasculature_cells` | 4 |
| `MT-ND5` | `Inhibitory_neurons` | 1 |
| `NCOA1` | `OPCs` | 1 |
| `RPL11` | `Astrocytes`; `Excitatory_neurons`; `Microglia`; `Oligodendrocytes` | 4 |
| `RPL15` | `Astrocytes` | 1 |
| `RPL38` | `Inhibitory_neurons` | 1 |
| `RPLP1` | `Astrocytes`; `Inhibitory_neurons` | 2 |
| `RPS13` | `Excitatory_neurons` | 1 |
| `RPS15` | `Inhibitory_neurons`; `OPCs` | 2 |
| `SELENOW` | `Excitatory_neurons` | 1 |
| `UQCR10` | `Excitatory_neurons` | 1 |
| **Total** | **25 genes** | **47** |

Common-variant, coding, and rare-variant evidence is searched once per gene
and then referenced by every context for that gene. Molecular-QTL evidence is
evaluated per `key_driver + broad_network` because context match matters. One
GWAS locus repeated across contexts is not independent replication.

Expanding from the seven-gene experimental starter panel to all 25 genes adds little
computational cost when the precomputed fine-mapping and colocalization tables
are filtered in one pass. The material extra work is human review of 25 gene
searches and any candidate-specific custom reruns. Those reruns remain
conditional, so they do not justify restricting the primary scope.

## Phase 19 end state

This section defines the destination before the implementation steps.

### Scientific and technical end state

Production is technically complete when:

```text
validation_status = validated_complete
phase18_candidate_context_units = 47
phase18_unique_genes = 25
local_pilot_candidate_context_units = 47
local_pilot_unique_genes = 25
production_summary_rows = 47
candidate_locus_rows = 25
undeclared_output_files = 0
blocking_check_failures = 0
```

Every one of the 47 candidate-context units must have:

- a terminal overall grade of `strong`, `moderate`, `weak`, `none_found`, or
  `not_assessable`;
- separate route statuses for common/fine-mapped, eQTL, sQTL, rare-variant,
  and, where applicable, mtDNA evidence;
- explicit exact-context or fallback-context labels;
- source IDs, versions, checksums, and access dates;
- assessability and failure reasons;
- any conflicting or alternative-gene evidence; and
- one permitted, noncausal interpretation statement.

No positive biological result is required for technical completion. A fully
audited set of 47 negative or unassessable results can be a valid completed
phase.

### Files changed to establish this plan

| Existing file | Change made now |
|---|---|
| `docs/phase_19_genetic_support/tier1/human_genetic_support_plan.md` | Rewritten from a WP5 guide into this Phase 19 end-state and implementation contract. |
| `docs/analysis/kda_phase_18/phase18_key_driver_cross_validation_guide.md` | WP5 now points to this renamed Phase 19 plan. |

### Files Phase 19 implementation will add

| File | End-state purpose |
|---|---|
| `config/phase19_genetic_support.yml` | Freeze the input identities, complete 25-gene scope, source registry, phenotype/context hierarchy, thresholds, priors, routes, output schemas, paths, and analysis version. |
| `config/phase19_local_production_execution.yml` | Define the 24-GB local production-equivalent resource profile, one-at-a-time custom colocalization, scratch paths, and hardware safety gates. |
| `requirements/phase19_genetic_support.txt` | Pin the Python packages used by the Tier 1 public-summary workflow. |
| `scripts/19_run_genetic_support.py` | Validate inputs, construct manifests/loci, extract Tier 1 evidence, grade assessability, make figures, and publish the validated bundle. |
| `tests/test_phase19_genetic_support.py` | Unit and end-to-end tests for scope, grading, assessability, H0-H4 safeguards, output counts, and artifact hashes. |

No separate hand-edited candidate TSV will be added to source control. The
script constructs it from the hash-frozen Phase 18 file, and the tests verify
the expected keys and counts.

### Existing files Phase 19 implementation will modify

| File | Tracking | Required end-state change |
|---|---|---|
| `scripts/run_pipeline.R` | Git-tracked | Register and dispatch the global `genetic_support` task, resolve the Phase 19 config path, and accept `local_production_equivalent` as a validated execution stage. |
| `config/minerva_shared.yml` | Git-tracked | Add the Phase 19 config path, external-data root, and `genetic_support` to allowed production task modes. |
| `config/local_pilot.yml` | Workstation-only; ignored by Git | Add the Phase 19 config path and permit the nonfinal local pilot task. |
| `renv.lock` | Git-tracked | No Tier 1 change. Pin `coloc` and `susieR` only if Tier 2 custom colocalization is authorized and implemented. |
| `.gitignore` | Git-tracked | Add an explicit ignore rule for `data/reference/phase19_genetic_support/` and permit the validated Phase 19 production result directory while continuing to ignore local pilot output. |

Tier 1 uses the version-pinned Python summary workflow. It does not install or
run `coloc`/`susieR`, because the public snapshot does not contain the regional
summary inputs required for a valid custom analysis. Those dependencies and
the prior-sensitivity route remain a separate Tier 2 implementation decision.

### Files deleted

None.

Phase 19 does not delete, overwrite, or edit:

- Phase 18 configuration or result files;
- the GENCODE v44 or HGNC frozen references;
- scripts or results from Phases 00-18;
- raw expression data;
- controlled-access genetics data; or
- an existing validated Phase 19 bundle.

A replacement Phase 19 run must use a new staging directory and publish only
after validation succeeds.

### External files added outside source control

Downloaded and manually staged genetics files go under:

```text
data/reference/phase19_genetic_support/
```

Before any download, implementation must add an explicit Git ignore rule for
this directory. Its end-state structure is:

```text
data/reference/phase19_genetic_support/
├── source_downloads/       # exact source files, unchanged
├── catalog_snapshots/      # dated query exports
├── regional_inputs/        # optional candidate-region GWAS/QTL/LD inputs
└── source_manifest.tsv     # versions, bytes, checksums, access, and paths
```

No access token, Synapse profile, participant-level genotype, CRAM/BAM, VCF,
or controlled phenotype file may be copied into the repository.

### Generated production files

The final directory is flat and contains exactly the files declared in the
output contract below. Temporary harmonized tables, model objects, caches,
and logs remain in scratch and are not copied into the final bundle.

### Pipeline registration

```text
task_mode: genetic_support
scope: global
stable_task_id: global:genetic_support
output_schema: human_genetic_support_tier1_v1
scientific_script: scripts/19_run_genetic_support.py
upstream_file_contract: Phase 18 key-driver selection v2
default_execution_stage: local_production_equivalent
fallback_execution_stage: minerva_production
```

Both environment YAML files add:

```yaml
project:
  phase19_genetic_support_config: config/phase19_genetic_support.yml

scope:
  allowed_task_modes:
    - genetic_support
```

The global task rejects `--rds-id`. Phase 18 is not currently a registered
task in `scripts/run_pipeline.R`; Phase 19 therefore validates the Phase 18
file contract directly rather than inventing a pipeline dependency that does
not exist.

The default local production command will be:

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/phase19_local_production_execution.yml \
  --phase genetic_support
```

The shared config name reflects the existing repository convention. The
execution config and saved status—not the filename `minerva_shared.yml`—state
where the task actually ran.

## New-data requirement and storage plan

### Is new data required?

Yes. The existing repository is sufficient to define the candidates and gene
loci, but it does not contain the human GWAS fine-mapping, AD-QTL
colocalization, or rare-variant evidence needed to answer Phase 19.

The minimum production study uses external summary-level results. It does not
require new biological sample collection or participant-level sequencing.

### Existing local inputs

| File | Role | Bytes | SHA-256 |
|---|---|---:|---|
| `results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv` | Frozen candidates and contexts | 63,161,765 | `b917f70e6edcdf030f63e88ba8fbc5b22b80714599c12c80ea449e8c38bd51d8` |
| `data/reference/gencode/gencode.v44.basic.annotation.gtf.gz` | GRCh38 gene coordinates/transcripts | 29,570,410 | `3e52f82c63f8fd860bf632ccde10441c05751f4c342ad08c0a98e9e2700171a5` |
| `data/reference/hgnc/hgnc_complete_set_2026-06-05.txt` | Approved symbols and aliases | 16,739,920 | `f3051e4aa6fac82166e1c26638d0077a95b0f66ab62a03e18bb35eb613e40a90` |
| **Total** | Existing frozen local input | **109,472,095 bytes (about 104.4 MiB)** | — |

### External source tiers

| Tier | Data to obtain | Required for Phase 19? | Size planning |
|---|---|---|---|
| 1 | AD GWAS top-locus/fine-mapping summary, precomputed AD-xQTL colocalization summary, dated catalog exports, and published rare-variant result tables | Yes | Usually MB to low-GB scale; reserve 20 GB for source files and 40 GB scratch until exact inventory is frozen. |
| 2 | Full candidate-region GWAS/QTL statistics, matching fine-mapping models, and ancestry-matched LD for unresolved comparisons | Conditional | Often tens to hundreds of GB if whole resources are staged. Download only explicit child files after inventory; require free space of at least `2.2 x compressed bytes` for extraction and scratch. |
| 3 | Individual-level ADSP WES/WGS and phenotypes | No; outside Phase 19 | Multi-terabyte and controlled access; do not acquire for this plan. |

The capacity numbers are reservations, not claims about current Synapse
container sizes. Container contents and versions can change. The exact child
file bytes must be obtained with an inventory command and written into
`source_manifest.tsv` before download. A recursive container download is
prohibited until its aggregate byte count and available disk space have been
reviewed.

### Primary external resources

Inventory these current resource containers, then freeze exact child file IDs
and versions in the Phase 19 config:

```text
syn69696846  AD fine-mapping results
syn69865824  unified top-locus fine-mapping summary
syn69865816  AD-molecular-QTL colocalization results
syn69670630  AD-molecular-QTL colocalization models, conditional
syn69670592  molecular-QTL fine-mapping models/results, conditional
syn69670652  ADSP European-ancestry LD reference, conditional
```

The [FunGen-AD AD GWAS resource](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/gwas/AD_GWAS/)
documents GRCh38 harmonization, fine-mapped AD loci, and an ADSP European-
ancestry LD panel. The corresponding
[eQTL](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/eQTL/),
[sQTL](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/sQTL/), and
[caQTL](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/caQTL/)
pages document molecular-QTL and AD-integration resources.

Use the GWAS Catalog and NIAGADS only through dated saved exports for the
formal run. A live web result is discovery material until it is frozen and
registered.

### Required source manifest fields

```text
schema_version
dataset_id
resource
source_url_or_synapse_id
child_file_id
child_file_version
source_filename
local_relative_path
access_class
data_use_terms
phenotype
phenotype_tier
case_definition
ancestry
n_total
n_cases
n_controls
brain_region
cell_type
qtl_type
genome_build
effect_allele_definition
compressed_bytes
uncompressed_bytes_if_known
sha256
retrieval_date
primary_or_sensitivity
approved_for_analysis
exclusion_reason
```

Do not infer ancestry, genome build, sample size, or allele convention from a
filename.

## Frozen analysis design

### Phenotype hierarchy

1. **Primary:** clinically anchored late-onset AD case-control GWAS.
2. **Secondary:** age at onset, amyloid, tau, neuropathology, cognitive
   decline, or another explicitly AD-related endophenotype.
3. **Sensitivity:** proxy-AD or broad-dementia GWAS.

These phenotypes remain separate. A sensitivity phenotype cannot replace a
missing or unfavorable primary result.

### Molecular-QTL context hierarchy

| Phase 18 network | Primary QTL context | Labeled fallback |
|---|---|---|
| `Astrocytes` | Astrocyte | major-cell-type astrocyte, then bulk brain |
| `Excitatory_neurons` | Excitatory neuron | neuron, then bulk brain |
| `Inhibitory_neurons` | Inhibitory neuron | neuron, then bulk brain |
| `Microglia` | Microglia | myeloid/microglia bulk, then bulk brain |
| `OPCs` | OPC | oligodendrocyte lineage, then bulk brain |
| `Oligodendrocytes` | Oligodendrocyte | oligodendrocyte lineage, then bulk brain |
| `Vasculature_cells` | matched endothelial or pericyte subtype | vascular aggregate, then bulk brain |

`CAMs` and `T_cells` currently contribute no displayed candidate units. Their
mapping rules are still frozen in the YAML before implementation so an
upstream-version change cannot trigger an ad hoc rule.

An oligodendrocyte result is not exact OPC evidence. A bulk-brain result is
not cell-type replication.

### Evidence routes

Four nuclear-gene routes are retained separately:

1. a fine-mapped AD variant with a coding or splice consequence in the
   candidate;
2. AD GWAS colocalization with a candidate eQTL or sQTL;
3. a noncoding AD signal connected through a coherent regulatory chain,
   including caQTL evidence; and
4. a corrected and preferably replicated rare-variant gene association.

For mtDNA genes, standard nuclear cis-eQTL/LD logic is not forced. The
separate route covers mtDNA variants, heteroplasmy, haplogroup, copy number,
tissue, depth, and NUMT handling.

### Primary statistical rules

- Common-variant discovery requires the source study's genome-wide rule;
  `P < 5e-8` is the default.
- Gene-burden evidence must pass the study-wide correction across the genes
  and masks tested by the source study.
- Primary colocalization support requires `PP.H4 >= 0.80` and
  `PP.H4 / (PP.H3 + PP.H4) >= 0.80`.
- Strong colocalization must also pass prior sensitivity, locus QC, and
  multi-signal handling when multiple signals are plausible.
- Direct coding/splice evidence uses `variant PIP >= 0.50` as the working
  strong threshold, with exact PIP, credible-set coverage, purity, transcript,
  and competing variants retained.
- `0.50 <= PP.H4 < 0.80` is suggestive, not strong.
- The conditional H4 value is missing when `PP.H3 + PP.H4` is effectively
  zero; it is never forced to zero or one.

All continuous statistics are retained. Thresholds classify evidence but do
not replace the underlying estimates or uncertainty.

### Direction convention

After allele harmonization:

```text
GWAS beta > 0: the effect allele increases AD risk
QTL beta  > 0: the same effect allele increases the molecular trait
```

`sign(GWAS beta x QTL beta) > 0` means that the allele increasing the
molecular trait is associated with higher AD risk. A negative product means
it is associated with lower risk. This describes allele direction; it does
not prove mediation or predict the consequence of a therapeutic intervention.

KDA selection alone does not predict the sign of a causal expression effect.

### Evidence grades

| Grade | Required interpretation |
|---|---|
| `strong` | Well-fine-mapped coding/splice evidence; robust AD-candidate eQTL/sQTL colocalization with strong QC, preferably exact-context; or corrected and independently replicated rare-variant association. |
| `moderate` | Convergent credible mappings; corrected but unreplicated rare-variant evidence; or robust colocalization in a biologically relevant fallback context. |
| `weak` | Nearest-gene assignment, gene-body overlap alone, TWAS alone, nominal association, uncorrected burden, or incomplete regulatory chain. |
| `none_found` | The prespecified sources were searched and assessable but yielded no convincing gene-level support. |
| `not_assessable` | Missing measurement, unresolved build/alleles, sparse locus overlap, unsuitable LD, incomplete metadata, or unavailable required data prevented the route from answering the question. |

The strongest qualifying grade is reported, but conflicting mappings and
alternative genes remain visible. APOE is a positive control, not a threshold
calibrator, and its complex LD region is handled separately.

## Construction and analysis workflow

### Task 1: freeze definitions and software

**Why:**

Candidate selection, source priority, and grading rules must be fixed before
candidate-specific evidence is reviewed.

**Inputs:**

- this approved plan;
- Phase 18 config and candidate-result file;
- existing GENCODE v44 and HGNC references; and
- the current R environment and audited local hardware.

**Steps:**

1. create `config/phase19_genetic_support.yml`;
2. create `config/phase19_local_production_execution.yml` with the frozen
   local memory, worker, scratch, and free-space gates;
3. record the frozen input hashes and expected 47/25 counts;
4. encode one common 47-unit selection rule for local validation and
   production;
5. freeze phenotype, context, evidence-route, grading, and status precedence;
6. freeze the colocalization priors `p1 = 1e-4`, `p2 = 1e-4`, and primary
   `p12 = 5e-6`;
7. freeze sensitivity values `p12 = 1e-6, 5e-6, 1e-5`;
8. freeze paths, schemas, output names, numeric tolerances, and plot rules;
9. pin the Tier 1 Python dependencies; defer `coloc` and `susieR` to Tier 2; and
10. set `definitions_frozen = TRUE` only after all fields validate and none is
   `TBD`.

**Outputs:**

```text
config/phase19_genetic_support.yml
config/phase19_local_production_execution.yml
genetic_support_analysis_manifest.tsv
```

**Ready when:**

The complete analysis contract has no result-dependent choice or unresolved
placeholder.

### Task 2: inventory and acquire external sources

**Why:**

Container IDs alone do not define immutable analysis inputs. Exact child
files, versions, sizes, permissions, and checksums are required.

**Inputs:**

- the source priorities in this plan;
- approved Synapse/NIAGADS access; and
- available storage.

**Steps:**

1. authenticate through a local Synapse profile or environment token without
   writing credentials to commands, scripts, logs, or Git;
2. inventory each required container in long form and save the listing;
3. choose explicit child files for the Tier 1 route;
4. calculate aggregate compressed size before downloading;
5. verify free space against the storage rule;
6. accept applicable data-use terms;
7. download explicit file IDs, not mutable aliases;
8. preserve source filenames and bytes unchanged;
9. calculate SHA-256 for every local file;
10. create dated GWAS Catalog/NIAGADS query exports;
11. freeze the source manifest and config entries; and
12. leave Tier 2 files absent unless Task 7 authorizes a candidate-specific
    rerun.

The supported Synapse CLI pattern is documented in the
[Synapse command-line client guide](https://python-docs.synapse.org/en/stable/tutorials/command_line_client/).
Inventory precedes `synapse get`; `synapse get -r` is not used without a
reviewed aggregate size.

**Outputs:**

```text
data/reference/phase19_genetic_support/source_manifest.tsv
data/reference/phase19_genetic_support/source_downloads/
data/reference/phase19_genetic_support/catalog_snapshots/
genetic_support_dataset_registry.tsv
genetic_support_input_inventory.tsv
genetic_support_source_checks.tsv
```

**Ready when:**

Every required source has an explicit version, byte count, checksum, access
classification, phenotype/context metadata, and approved local path.

### Task 3: validate Phase 18 and construct candidate manifests

**Why:**

External evidence is interpretable only for the exact candidate set that
Phase 18 selected.

**Inputs:**

- hash-frozen Phase 18 result and config; and
- expected full-scope counts from the Phase 19 config.

**Steps:**

1. validate both Phase 18 hashes before reading candidate rows;
2. require `top5_display` and all identity/ranking/context columns;
3. filter `top5_display == TRUE` without reranking;
4. construct the unique `key_driver + broad_network + case_id` key;
5. require 47 unique context units and 25 genes;
6. require all 47 candidate-context keys and all 25 genes;
7. retain the Phase 18 rank, evidence tier, class, and source row identity;
8. label nuclear and mtDNA units; and
9. write the manifest before joining external evidence.

**Outputs:**

```text
genetic_support_candidate_manifest.tsv
```

**Ready when:**

The output reproduces the frozen 47/25 counts, has no duplicate key, and every
row traces to a Phase 18 source row.

### Task 4: resolve stable genes and GRCh38 loci

**Why:**

Gene aliases and inconsistent genome builds can create false matches.

**Inputs:**

- candidate manifest;
- GENCODE v44 GRCh38 GTF; and
- frozen HGNC snapshot.

**Steps:**

1. resolve every nuclear candidate to an approved symbol and stable Ensembl
   gene ID;
2. retain aliases and mapping evidence;
3. extract chromosome, gene start/end, strand, and TSS on GRCh38;
4. define a catalog discovery interval of gene body plus 1 Mb on each side;
5. use the complete source fine-mapping block or prespecified cis region for
   formal analysis rather than the discovery interval;
6. flag the APOE GRCh38 region for separate handling;
7. identify mtDNA candidates and the mitochondrial reference requirements;
8. preserve other plausible genes at each locus; and
9. stop on unresolved or one-to-many primary identities.

**Outputs:**

```text
genetic_support_candidate_loci.tsv
```

**Ready when:**

Exactly 25 genes have a unique primary identity or a blocking unresolved
status, all coordinates have a recorded reference build, and no alias match is
implicit.

### Task 5: extract common-variant and fine-mapping evidence

**Why:**

A nearby GWAS association must be separated from evidence that actually
implicates the candidate gene.

**Inputs:**

- candidate loci;
- frozen catalog snapshots; and
- AD fine-mapping summaries.

**Steps:**

1. search the prespecified AD phenotype tiers once per gene;
2. retain study, ancestry, samples, phenotype, lead variant, alleles, effect,
   uncertainty, P value, and correction;
3. identify every source locus/block overlapping the discovery interval;
4. extract all signals and credible sets, not only the lead variant;
5. retain variant PIP, credible-set coverage/purity, method, ancestry, and LD
   source;
6. annotate coding/splice and regulatory consequences on documented
   transcripts;
7. record mappings to the candidate and to competing genes; and
8. assign controlled mapping categories.

Controlled mapping categories are:

```text
coding_candidate
splice_candidate
promoter_candidate
enhancer_candidate
colocalized_eqtl_candidate
colocalized_sqtl_candidate
caqtl_regulatory_chain_candidate
nearest_gene_only
mapped_to_other_gene
unresolved
```

**Outputs:**

```text
genetic_support_search_log.tsv
genetic_support_common_variant_evidence.tsv.gz
```

**Ready when:**

Every nuclear gene has a documented search and every retained signal preserves
its complete fine-mapping and competing-gene context.

### Task 6: extract precomputed AD-QTL colocalization

**Why:**

Precomputed FunGen-AD integration is the shortest primary route and avoids
unnecessary reanalysis when the harmonized result already exists.

**Inputs:**

- candidate manifest and loci;
- registered precomputed AD-xQTL results; and
- frozen context hierarchy.

**Steps:**

1. match candidates by stable Ensembl ID, handling version suffixes only under
   a recorded convention;
2. extract eQTL and sQTL results first, then caQTL regulatory chains;
3. assign `exact`, `lineage_fallback`, `bulk_brain_fallback`, or
   `context_mismatch`;
4. retain every independent GWAS-signal and QTL-signal pair;
5. record the supplied method and all available posterior hypotheses;
6. verify that both traits have a detectable regional signal;
7. inspect credible-set overlap and alternative genes;
8. calculate direction only when alleles and effects are aligned; and
9. write an explicit route status even when no result is present.

TWAS, qTWAS, or cTWAS may be retained as supplementary evidence. They do not
replace colocalization.

**Outputs:**

```text
genetic_support_colocalization.tsv.gz
genetic_support_colocalization_qc.tsv
```

**Ready when:**

Every candidate-context unit has separate eQTL and sQTL assessability/status,
and no fallback context is labeled as exact replication.

### Task 7: run only justified custom colocalization

**Why:**

Some candidate comparisons may be absent or ambiguous in the precomputed
resource. A rerun is useful only when dense, compatible inputs are available.

**Inputs:**

- unresolved comparisons from Task 6;
- complete regional GWAS and QTL statistics;
- trait sample sizes and types;
- ancestry/build-matched LD where needed; and
- frozen priors and locus definitions.

**Steps:**

1. create a rerun decision row for every unresolved comparison;
2. authorize a rerun only when it addresses a prespecified missing or
   methodologically unsuitable result;
3. harmonize both datasets to GRCh38 and
   `chromosome:position:ref:alt`;
4. split multiallelic records and left-normalize indels;
5. align effect alleles, flip beta on swaps, and resolve or drop strand-
   ambiguous variants using frequency information;
6. retain dense regional coverage without P-value filtering;
7. record raw, post-QC, and shared variant counts plus lead retention;
8. use `coloc.susie` when multiple signals and suitable LD are available;
9. use `coloc.abf` only when a single-signal assumption is defensible or as a
   declared sensitivity;
10. report H0-H4, all signal pairs, convergence, credible-set purity, and LD
    provenance;
11. rerun the three frozen `p12` values and a defensible alternate locus
    definition; and
12. label the comparison `not_assessable` rather than switching to a favorable
    nearby result when QC fails.

Minimum harmonized input fields are:

```text
chromosome
position
ref
alt
effect_allele
other_allele
beta
standard_error
p_value
variant_id
effect_allele_frequency_or_maf
imputation_info_if_available
sample_size
```

For case-control GWAS, retain the case fraction. For quantitative QTLs,
retain phenotype variance information or the inputs required for the selected
method. P-value-only colocalization is sensitivity evidence, not the primary
directional result.

**Outputs:**

```text
genetic_support_colocalization.tsv.gz
genetic_support_colocalization_qc.tsv
genetic_support_coloc_prior_sensitivity.tsv.gz
```

**Ready when:**

Every authorized rerun passes build, allele, coverage, signal, LD, convergence,
and prior-sensitivity checks, or has a terminal failure reason.

### Task 8: review rare variants and mtDNA evidence

**Why:**

Rare damaging variants can implicate a gene even when common cis-regulatory
evidence is absent, while mtDNA genes require a different association model.

**Inputs:**

- registered ADSP/NIAGADS publications and summary results;
- paper supplements; and
- the six mtDNA candidates.

**Steps for nuclear genes:**

1. verify that the gene was actually tested;
2. distinguish single-variant, burden, SKAT-O, STAAR, and other gene-level
   tests;
3. record annotation mask, MAF/MAC threshold, variants, cumulative MAC,
   ancestry, samples, phenotype, covariates, relatedness, and platform;
4. record the correction across genes and masks;
5. determine whether the result passes that study-wide rule;
6. identify an independent replication cohort rather than a reused sample;
7. disclose one-variant-driven aggregate results; and
8. never treat case-only carriers or damaging predictions as association.

**Steps for mtDNA genes:**

1. search mtDNA SNV/indel, heteroplasmy, heteroplasmy-burden, haplogroup, and
   copy-number studies;
2. retain mitochondrial build, position, alleles, heteroplasmy threshold,
   depth, tissue, ancestry, and batch adjustment;
3. require documented NUMT handling;
4. separate tissue-specific from blood-derived evidence;
5. do not assign a genome-wide mtDNA copy-number association to one mtDNA
   gene; and
6. do not apply a nuclear LD panel or standard nuclear cis-colocalization to
   mtDNA.

**Outputs:**

```text
genetic_support_rare_variant_evidence.tsv
genetic_support_mtdna_evidence.tsv
```

**Ready when:**

Every candidate has a documented search, correction and assessability are
explicit, and mtDNA evidence uses mitochondrial-specific QC.

### Task 9: assign assessability, grades, and wording

**Why:**

The conclusion must follow frozen rules and must distinguish missing evidence
from evidence against a shared signal.

**Inputs:**

- all detailed route tables;
- source and QC checks; and
- the frozen grade/status precedence.

**Steps:**

1. assign each route one of `positive`, `no_shared_signal`,
   `distinct_signals`, `no_regional_signal`, `not_assessable`, or
   `not_searched`;
2. verify that `not_searched` is absent from a production-complete row;
3. select the best valid evidence using phenotype/context priority before
   evidence strength, not the smallest P value alone;
4. apply the frozen grade rules;
5. retain `context_matched`, `replicated`, and `conflicting_evidence` as
   separate fields;
6. carry shared gene-level results to multiple contexts without counting them
   as independent observations;
7. generate a noncausal interpretation statement; and
8. preserve all detailed rows behind the one-row-per-context summary.

**Outputs:**

```text
genetic_support_assessability.tsv
genetic_support_evidence_summary.tsv
```

**Ready when:**

The summary has exactly 47 unique rows and every grade and statement
reproduces mechanically from detailed evidence and frozen precedence.

### Task 10: create figures from validated tables

**Why:**

Figures must display saved evidence rather than reanalyze data.

**Inputs:**

- final evidence summary;
- detailed colocalization and fine-mapping results; and
- fixed display rules.

**Steps:**

1. create a candidate-by-evidence matrix separating coding, matched eQTL,
   sQTL, regulatory-chain, TWAS-only, rare-variant, and mtDNA routes;
2. use a distinct symbol for `not_assessable` rather than plotting it as no
   evidence;
3. separate APOE or use a scale that does not hide other genes;
4. create one multipage locus PDF for strong/moderate colocalizations;
5. include GWAS and QTL patterns, credible sets, context, method, and source;
6. create a documented placeholder page when no locus qualifies; and
7. write all plotted values to one figure-data table.

**Outputs:**

```text
genetic_support_figure_data.tsv.gz
genetic_support_evidence_matrix.pdf
genetic_support_evidence_matrix.png
genetic_support_locus_plots.pdf
```

**Ready when:**

Every plotted value and label traces to a validated output row and the plotting
step does not refit or regrade evidence.

### Task 11: validate and publish atomically

**Why:**

A phase is complete only when an output-only validator can reproduce its file
contract, keys, counts, statuses, grades, and hashes.

**Inputs:**

- every scientific output;
- expected schemas and counts; and
- artifact/status rules.

**Steps:**

1. write all scientific files to a unique staging directory;
2. validate schemas, keys, row counts, enums, numeric ranges, and provenance;
3. recalculate grades from detailed tables;
4. require 47 terminal production summary rows;
5. write stage and blocking-check tables;
6. create the artifact manifest for every declared file except the artifact
   manifest and final status file;
7. run the independent output-only test path;
8. require zero blocking failures and zero undeclared files;
9. write the final status last; and
10. atomically rename staging to the production directory.

**Outputs:**

```text
genetic_support_stage_status.tsv
genetic_support_checks.tsv
genetic_support_artifacts.tsv
genetic_support_status.tsv
```

**Ready when:**

The published directory is flat, immutable, complete, independently
validated, and has `validation_status = validated_complete`.

## Output and file contract

Final production root:

```text
results/minerva_production/19_genetic_support_tier1/
```

| File | Required content |
|---|---|
| `genetic_support_analysis_manifest.tsv` | One frozen analysis row with versions, hashes, scopes, thresholds, priors, paths, and software identity. |
| `genetic_support_candidate_manifest.tsv` | Exactly 47 Phase 18 candidate-context rows across exactly 25 unique genes in both local validation and production. |
| `genetic_support_candidate_loci.tsv` | Exactly 25 gene rows with approved/stable identities, GRCh38 coordinates, windows, and mtDNA/APOE flags. |
| `genetic_support_dataset_registry.tsv` | One row per registered external dataset or study, including phenotype, context, samples, ancestry, build, access, and eligibility. |
| `genetic_support_input_inventory.tsv` | Every local scientific input with path, bytes, SHA-256, source ID/version, and validation state. |
| `genetic_support_source_checks.tsv` | Input identity, schema, build, access, count, and provenance checks. |
| `genetic_support_search_log.tsv` | Every gene, route, database/publication query, date, query text, and terminal search status. |
| `genetic_support_common_variant_evidence.tsv.gz` | Long-form GWAS/fine-mapping signals, credible sets, variants, PIP, consequences, mappings, and competing genes. |
| `genetic_support_colocalization.tsv.gz` | Precomputed and custom signal-pair results with H0-H4, method, context match, direction, and source. |
| `genetic_support_colocalization_qc.tsv` | Coverage, shared variants, lead retention, allele operations, signal status, LD, convergence, and assessability. |
| `genetic_support_coloc_prior_sensitivity.tsv.gz` | All authorized custom comparisons under the three frozen `p12` values and locus definitions. |
| `genetic_support_rare_variant_evidence.tsv` | Gene-level/single-variant tests, masks, MAF/MAC, correction, replication, driver variants, and status. |
| `genetic_support_mtdna_evidence.tsv` | mtDNA variant, heteroplasmy, haplogroup, copy-number, tissue, depth, build, NUMT, and interpretation fields. |
| `genetic_support_assessability.tsv` | Route-level positive/negative/ambiguous/unassessable status and exact reason for every applicable candidate-context route. |
| `genetic_support_evidence_summary.tsv` | Exactly 47 final rows with best valid evidence, grade, context, replication/conflict flags, sources, and permitted wording. |
| `genetic_support_figure_data.tsv.gz` | Every value, label, order, and status used in the matrix and locus figures. |
| `genetic_support_evidence_matrix.pdf` | Vector evidence matrix for all 47 candidate-context units. |
| `genetic_support_evidence_matrix.png` | Raster review copy of the same evidence matrix. |
| `genetic_support_locus_plots.pdf` | Multipage strong/moderate locus plots or one documented no-qualifying-locus page. |
| `genetic_support_stage_status.tsv` | Planned, completed, skipped, failed, and reused stages with dependencies and timestamps. |
| `genetic_support_checks.tsv` | Blocking and nonblocking checks with observed and expected values. |
| `genetic_support_artifacts.tsv` | Declared paths, schemas, rows, bytes, SHA-256, and validation states. |
| `genetic_support_status.tsv` | One final technical/scientific status row, written last. |

The final directory contains exactly these 23 files. Every TSV begins with
`schema_version`.

`genetic_support_artifacts.tsv` cannot contain its own final hash. It hashes
every declared output except itself and `genetic_support_status.tsv`; the
status file stores the completed artifact-manifest hash.

### Required final summary fields

```text
schema_version
key_driver
broad_network
case_id
ensembl_gene_id
phase18_within_case_rank
phase18_evidence_tier
analysis_scope
genome_origin
common_variant_status
best_gwas_phenotype
best_gwas_study
best_locus_id
best_mapping_category
best_variant
best_variant_pip
coding_support
eqtl_status
best_eqtl_pp_h4
sqtl_status
best_sqtl_pp_h4
best_matched_context_pp_h4
best_coloc_method
best_coloc_context
context_match_level
best_coloc_direction
caqtl_regulatory_chain
twas_only_support
rare_variant_status
rare_variant_best_p
rare_variant_corrected
rare_variant_replicated
mtdna_evidence_status
genetic_evidence_grade
context_matched
conflicting_evidence
assessability_summary
interpretation
source_ids
analysis_version
analysis_date
```

Fields beginning with `best` follow the frozen phenotype and context hierarchy
and then methodological validity. They are not selected solely by the largest
posterior or smallest P value.

## Local pilot and tests

The local pilot constructs all 47 candidate-context units and uses either
small source-compatible extracts or deterministic synthetic external-evidence
fixtures. It validates software and contracts only; it cannot produce Phase
19 scientific evidence. No candidate is excluded merely to make the pilot
smaller.

The test suite must include:

- exact reconstruction of 47 candidate-context units and 25 genes in both
  local and production modes;
- failure on changed Phase 18 hashes or duplicated candidate keys;
- symbol/Ensembl mapping, including aliases and mtDNA genes;
- allele match, swap, complement, swap-complement, ambiguous, and mismatch
  cases;
- beta sign flips on effect-allele swaps;
- indel normalization and build mismatch failures;
- no P-value filtering of a colocalization locus;
- single-signal and multi-signal synthetic colocalization;
- H4 conditional-posterior zero-denominator handling;
- all three prior-sensitivity values;
- exact versus fallback context classification;
- `distinct_signals`, `no_regional_signal`, and `not_assessable` cases;
- grade precedence and conflicting-evidence retention;
- mtDNA-specific routing without nuclear LD;
- a complete-null fixture that still validates technically;
- evidence-matrix generation with distinct `not_assessable` display;
- exact 23-file output contract and undeclared-file failure;
- local RAM/disk escalation gates and one-custom-locus worker enforcement;
- identical scientific fingerprints under local and Minerva execution
  profiles;
- artifact hash reproduction; and
- output-only validation without source or model objects.

Pilot completion requires:

```text
validation_status = validated_complete_pilot
candidate_context_units = 47
unique_genes = 25
scientific_claim_authorized = false
```

## Production execution gates

Production must not begin until:

- [ ] this plan is approved;
- [ ] all source-controlled implementation files exist;
- [ ] if Tier 2 is authorized, `renv.lock` includes the approved colocalization software;
- [ ] the Phase 18 source hashes and 47/25 counts validate;
- [ ] the full-manifest local pilot passes every blocking test;
- [ ] exact Tier 1 source child IDs, versions, sizes, and checksums are frozen;
- [ ] source access and data-use terms permit the planned analysis;
- [ ] the selected local or Minerva execution profile passes its RAM, disk,
  scratch, and worker gates;
- [ ] phenotype, context, prior, and grade rules remain frozen;
- [ ] every planned production route is searchable or has a prespecified
  assessability rule; and
- [ ] the production output directory does not already contain a validated
  bundle.

Custom regional analysis has an additional gate:

- [ ] both GWAS and QTL have complete dense regional statistics;
- [ ] trait type, samples, effects, SEs, alleles, frequencies, and build are
  known;
- [ ] suitable ancestry-matched LD is available when required;
- [ ] the rerun reason is recorded before its result is viewed; and
- [ ] aggregate data size and scratch capacity have been reviewed.

## Required QC and stopping rules

### Candidate and source QC

- [ ] Candidate keys and counts reproduce the hash-frozen Phase 18 file.
- [ ] Approved symbols and stable Ensembl IDs are explicit.
- [ ] Coordinates and mitochondrial reference use recorded builds.
- [ ] Every dataset has accession/version, checksum, phenotype, ancestry,
  samples, and allele convention.
- [ ] Primary/sensitivity phenotypes and exact/fallback contexts are labeled.
- [ ] Cohort overlap and nonindependence are documented.

### Fine-mapping QC

- [ ] All source signals and credible sets in the locus were examined.
- [ ] Variant PIP is not presented as gene probability.
- [ ] Coding/splicing consequences use documented transcripts.
- [ ] Noncoding mapping has an explicit evidence chain.
- [ ] Other plausible genes remain visible.

### Colocalization QC

- [ ] Both traits have dense, complete regional data when custom analysis is
  used.
- [ ] Build, variants, alleles, and beta directions are harmonized.
- [ ] Variant losses and lead-variant retention are reported.
- [ ] Both regional signal strengths were checked.
- [ ] Multiple signals were handled or the limitation is explicit.
- [ ] LD is ancestry/build/allele matched.
- [ ] H0-H4 and prior/locus sensitivities are retained.
- [ ] Exact context and fallback context are not conflated.

### Rare-variant and mtDNA QC

- [ ] The gene was actually tested.
- [ ] Test, mask, MAF, MAC, study-wide correction, and replication are known.
- [ ] Case-only observation is not called association.
- [ ] A one-variant-driven burden is disclosed.
- [ ] mtDNA depth, heteroplasmy, tissue, haplogroup, build, and NUMT handling
  are recorded where applicable.

Stop and use `not_assessable` when build/alleles cannot be resolved, a gene or
trait was not measured, locus overlap is sparse, required metadata are
missing, or suitable LD is unavailable. Do not repair a failed comparison by
switching to a favorable nearby gene, phenotype, tissue, or prior.

## Interpretation and reporting boundary

Acceptable wording:

> The AD association and the astrocyte eQTL for X showed evidence of a shared
> regional signal under the prespecified prior, supporting X as a candidate
> effector gene at this locus. Colocalization does not establish mediation.

> X was nearest to the lead variant, but fine mapping and molecular-QTL
> analyses did not specifically implicate X; this was graded as weak support.

> No convincing genetic support for X was found in the prespecified,
> assessable sources. This does not exclude a trans-acting or
> context-dependent role.

Prohibited wording:

```text
X is an AD gene because it is near a GWAS SNP.
X is causal because H4 is high.
X is mutated in AD patients.
The absence of a GWAS signal proves X is not involved in AD.
```

## Completion checklist

Phase 19 is complete only when:

- [ ] the production candidate manifest contains exactly 47 unique units and
  25 genes;
- [ ] all 25 loci are resolved or have a terminal blocking identity status;
- [ ] all required external sources are versioned, sized, checksummed, and
  access-compliant;
- [ ] common/fine-mapped evidence was screened for every applicable gene;
- [ ] exact and fallback eQTL/sQTL colocalization was assessed for every
  applicable context;
- [ ] every custom analysis has full harmonization, locus, LD, posterior, and
  sensitivity QC;
- [ ] rare-variant evidence was searched for every gene;
- [ ] all six mtDNA genes used the mitochondrial-specific route;
- [ ] `genetic_support_evidence_summary.tsv` has exactly 47 terminal rows;
- [ ] all 23 declared files exist and no undeclared file is present;
- [ ] every blocking check passes;
- [ ] the output-only validator reproduces keys, counts, grades, and hashes;
- [ ] `genetic_support_status.tsv` reports
  `validation_status = validated_complete`; and
- [ ] interpretations preserve the boundary between shared signal, gene
  mapping, mediation, causality, and absence of evidence.

Pilot completion alone does not satisfy this checklist.

## Resource and method references

- [FunGen-AD AD GWAS, fine-mapping, and LD resources](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/gwas/AD_GWAS/)
- [FunGen-AD eQTL resources](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/eQTL/)
- [FunGen-AD sQTL resources](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/sQTL/)
- [FunGen-AD caQTL resources](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/caQTL/)
- [NIAGADS open-access resources](https://www.niagads.org/open-access/)
- [NIAGADS Data Sharing Service](https://dss.niagads.org/)
- [ADSP data and publications](https://adsp.niagads.org/)
- [NHGRI-EBI GWAS Catalog guidance](https://www.ebi.ac.uk/gwas/docs/faq)
- [Synapse command-line client](https://python-docs.synapse.org/en/stable/tutorials/command_line_client/)
- [`coloc` input requirements](https://chr1swallace.github.io/coloc/articles/a02_data.html)
- [`coloc.susie` multi-signal workflow](https://chr1swallace.github.io/coloc/articles/a06_SuSiE.html)
- [FunGen-xQTL colocalization protocol](https://statfungen.github.io/xqtl-protocol/SuSiE_enloc.html)
- Giambartolomei C, et al. Bayesian test for colocalisation between pairs of
  genetic association studies using summary statistics. *PLoS Genetics*.
  2014. [doi:10.1371/journal.pgen.1004383](https://doi.org/10.1371/journal.pgen.1004383)
- Wallace C. A more accurate method for colocalisation analysis allowing for
  multiple causal variants. *PLoS Genetics*. 2021.
  [doi:10.1371/journal.pgen.1009440](https://doi.org/10.1371/journal.pgen.1009440)
