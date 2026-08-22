# Phase 19 human genetic support: overall plan and roadmap

**Status:** four planned workstreams executed locally; further validation routes remain optional  
**Current through:** 2026-08-21  
**Scope:** 25 ROSMAP Phase 18 key-driver genes in 47 candidate-context units

## Purpose

This is the root coordination document for Phase 19. It records the relationship
between workstreams, their cumulative scientific outcome, and the order of any
future work. Detailed scientific rules, input contracts, execution tasks, and
reports belong in the applicable subdirectory and are not duplicated here.

Phase 19 asks whether inherited human genetic variation supports any Phase 18
key-driver gene and, when possible, whether an AD or AD-endophenotype signal
shares a causal variant with a molecular QTL for that gene.

A gene is not considered validated merely because it is near a GWAS signal.
Classical shared-signal claims require compatible regional statistics or fitted
models, harmonized variants, and ancestry-appropriate LD.

## Documentation layout

### Tier 1: public summary evidence

- [Tier 1 plan](tier1/human_genetic_support_plan.md)
- [Tier 1 execution report](tier1/tier1_execution_report.md)
- Result root: results/minerva_production/19_genetic_support_tier1/

Tier 1 screens all 25 genes using public precomputed AD GWAS, fine-mapping,
xQTL, TWAS, and companion summary resources. It is the frozen baseline for
later workstreams.

### Tier 2: regional GWAS/QTL recovery

- [Tier 2 regional plan](tier2/tier2_regional_gwas_qtl_plan.md)
- [Tier 2 execution report](tier2/tier2_execution_report.md)
- [Classical colocalization recovery plan](tier2/tier2_classical_coloc_recovery_plan.md)
- [Recovery execution report](tier2/tier2_recovery_execution_report.md)
- [Why APOE and RPS15 remain unresolved](tier2/apoe_rps15_unresolved_colocalization_explained.md)
- Result roots:
  - results/minerva_production/19_genetic_support_tier2_regional/
  - results/minerva_production/19_genetic_support_tier2_recovery/

Tier 2 tests whether dense candidate-region GWAS/QTL statistics, fitted
fine-mapping models, and compatible LD can resolve comparisons left open by
Tier 1.

### Endophenotype GWAS/QTL extension

- [Extension plan](endophenotype_gwas_qtl_extension/endophenotype_gwas_qtl_extension_plan.md)
- [Execution report](endophenotype_gwas_qtl_extension/endophenotype_gwas_qtl_extension_execution_report.md)
- [Historical analysis that selected this workstream](endophenotype_gwas_qtl_extension/remaining_gwas_qtl_analyses_and_next_step.md)
- Result root: results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension/

This workstream tests CSF amyloid-beta 42, total tau, and p-tau181 GWAS so that
genes without a clinical-diagnosis GWAS signal can be evaluated against
phenotypes closer to AD pathology.

### OPC/RPS15 public-data recovery

- [OPC/RPS15 public-data-first plan](opc_rps15/opc_rps15_public_data_first_plan.md)
- [Execution report](opc_rps15/opc_rps15_public_data_first_execution_report.md)
- Result root: results/minerva_production/19_genetic_support_opc_rps15_public_recovery/

This workstream asks whether already-public, small, locally manageable QTL
resources can resolve RPS15 in OPCs or inhibitory neurons without waiting for
authors or downloading very large archives.

## Cumulative execution state

| Workstream | Frozen coverage | Technical outcome | Scientific outcome |
|---|---|---|---|
| Tier 1 | 25 genes; 47 candidate-context units | Validated 23-file bundle | APOE strong; COX7C and SELENOW weak/suggestive; mtDNA routes not assessable |
| Tier 2 regional | 54 nuclear eQTL/sQTL routes | Validated 23-file bundle | No route had classical H0-H4; no Tier 1 grade changed |
| Endophenotype extension | 25 genes; 3 biomarkers; 57 nuclear gate decisions | Validated complete | Only APOE passed GWAS/MAGMA gates; zero newly supported genes |
| OPC/RPS15 recovery | 31 eligible routes measured | Validated 24-file bundle | Six candidate-route signals, representing three bulk-brain tracks; zero resolved colocalizations and zero newly validated genes |

The current cumulative conclusion is:

- APOE is the only unique Phase 18 gene with a strong Tier 1 genetic grade.
- No completed extension added another validated gene.
- COX7C and SELENOW retain weak or suggestive summary support.
- RPS15 has suggestive regional/QTL evidence, but it is not validated because
  complete compatible models and source-matched LD were unavailable.
- The six mtDNA genes have not been tested by a suitable mitochondrial
  association design.
- Missing or incompatible data are not negative biological evidence.

Signal counts must not be inflated by counting the same source across multiple
candidate contexts as independent replication.

## Overall execution rules

Every new Phase 19 workstream must:

1. freeze the candidate genes, contexts, phenotypes, source hierarchy, and
   thresholds before inspecting target results;
2. preserve the immutable Tier 1 baseline and publish into a separate result
   directory;
3. distinguish no signal from not measured, unavailable, or model-incompatible;
4. require harmonized alleles, genome build, regional coverage, fitted
   multi-signal models where needed, and ancestry-compatible LD before claiming
   classical colocalization;
5. keep gene-level evidence separate from exact cell-context validation;
6. audit sample overlap with ROSMAP and prefer independent or
   leave-ROSMAP-out QTL evidence where available;
7. use local execution by default and acquire only candidate-region or
   otherwise bounded files that satisfy the storage contract;
8. avoid dependence on unpublished author-provided data as a critical path;
9. retain all prespecified candidates and terminal route statuses, including
   null and unassessable outcomes; and
10. report the number of unique supported genes separately from route,
    phenotype, and context counts.

The results/minerva_production name is a repository namespace. It does not mean
that computation must run on Minerva.

## Remaining roadmap

### Priority 1: public pQTL, PWAS, and TWAS support

Run a candidate-frozen coverage inventory for the 19 nuclear genes using
public brain or CSF protein resources and independent brain-expression models.
Primary biological interpretation should require a cis-pQTL or a reproducible
prediction model. TWAS/PWAS associations remain suggestive unless supported by
valid colocalization or fine-mapped high inclusion probability.

This has the best immediate combination of local feasibility and potential to
screen genes that lack a single genome-wide-significant regional GWAS variant.

### Priority 2: newer exact-cell-type QTL releases

Audit larger public single-nucleus eQTL and sQTL resources for the exact Phase
18 contexts, especially OPC RPS15 and ANKRD11, inhibitory-neuron RPS15 and
COX7C, and astrocyte APOE and COX7C. Proceed only when complete regional
statistics or fitted models and compatible LD are publicly obtainable. Donor
overlap with ROSMAP must be recorded.

### Priority 3: revisit unresolved colocalizations only when public inputs improve

APOE and RPS15 can be revisited if a public release supplies the missing
complete regional QTL statistics, fitted multi-signal models, or source-matched
LD. This route must not depend on an author response and must not substitute
generic LD merely to force an H4 estimate.

### Priority 4: dedicated mtDNA association

The six mitochondrial genes require a separate design covering mtDNA variants,
heteroplasmy, haplogroup, copy number, depth, NUMT handling, and mitochondrial
reference build. Nuclear cis-QTL logic and nuclear LD panels are not suitable
substitutes.

### Priority 5: controlled-data analyses

Rare-variant burden/SKAT-O and sex- or APOE-stratified GWAS/QTL analyses may
have high scientific value but require controlled data, larger storage, and
additional ancestry and interaction-model safeguards. They are later
workstreams rather than prerequisites for the completed public-data analyses.

## Ownership and file-placement rules

- This root directory contains only this cross-workstream overall plan.
- Tier-specific plans, reports, and explanations belong under tier1/ or tier2/.
- Endophenotype-specific plans, reports, and rationale belong under
  endophenotype_gwas_qtl_extension/.
- OPC/RPS15-specific plans and reports belong under opc_rps15/.
- Pipeline code remains under scripts/, configuration under config/, tests
  under tests/, compact references under data/reference/, and validated outputs
  under results/minerva_production/.
- A future detailed plan must be added to the relevant workstream directory
  before its execution; it must not be embedded into this overall roadmap.

## Overall completion definition

The four documented workstreams are technically complete when their frozen
scope, validation checks, output contracts, and execution reports pass. Phase
19 scientific validation is not declared complete merely because all public
routes terminate: additional genes may remain unresolved because the required
data do not exist publicly in a compatible form.

The current state is therefore:

- completed for the four registered local workstreams;
- one strongly supported unique gene, APOE;
- zero newly validated genes from the three extensions; and
- an explicit, prioritized roadmap for further GWAS/QTL and genetic analyses.
