# Remaining GWAS/QTL analyses and recommended next step

**Status:** recommendation; not yet executed  
**Evaluation date:** 2026-08-21  
**Scope:** the 25 unique ROSMAP Phase 18 key-driver genes represented by 47
gene-by-network candidate units

## Executive decision

Phase 19 has not exhausted all possible GWAS/QTL validation. It has completed
one important design: an Alzheimer disease case-control GWAS paired with
selected brain eQTL and sQTL resources for classical colocalization.

The recommended next analysis is:

> **Run a candidate-frozen AD endophenotype GWAS extension using the public
> 2026 CSF A-beta 42, total-tau, and p-tau181 GWAS summary statistics. First
> screen all 19 nuclear candidates for regional and corrected gene-based
> association. Only candidates with a qualifying regional single-variant
> signal should proceed to eQTL, sQTL, or pQTL fine-mapping and classical
> colocalization. A gene-based-only result should instead enter a separate
> TWAS/PWAS support route.**

This should be taken next because it:

- can identify genetically supported candidates missed by a heterogeneous
  clinical diagnosis GWAS;
- uses three quantitative traits that are closer to core AD pathology;
- has completely released summary statistics that can be analyzed locally;
- can evaluate all 19 nuclear candidates before expensive QTL/LD acquisition;
- preserves a strong signal-first colocalization standard; and
- has greater potential to support additional genes than resolving only the
  two current APOE and RPS15 routes.

This is a mechanism-specific extension. A result for tau or A-beta should be
reported as genetic support for that biomarker pathway, not automatically as
general AD-diagnosis validation.

## What the completed Phase 19 analysis established

The Tier 2 recovery evaluated 54 nuclear eQTL/sQTL routes. Its terminal states
were:

| Terminal state | Routes | Meaning |
|---|---:|---|
| `no_regional_gwas_signal` | 42 | The candidate region had no variant below the frozen genome-wide AD threshold in the Bellenguez diagnosis GWAS. |
| `no_regional_qtl_signal` | 4 | The AD region had a signal, but the complete tested eQTL region did not contain a qualifying candidate-gene eQTL. |
| `model_or_ld_incompatible` | 2 | Both regional AD and eQTL signals existed, but the QTL fine-mapping model and compatible QTL LD were unavailable. |
| `not_assessable` | 6 | The candidate splicing event was absent from the released conditional/model files, so measurement and signal status could not be resolved. |

The four nuclear genes with a genome-wide-significant regional signal in the
current diagnosis GWAS were `ANKRD11`, `APOE`, `COX7C`, and `RPS15`.

Their present status is:

| Gene/context | Current result | What remains possible |
|---|---|---|
| Astrocyte `APOE` | Strong regional AD signal and bulk-neocortex eQTL, but no compatible QTL fine-mapping/LD | Complete multi-signal colocalization if study-matched QTL LD or author-provided SuSiE models can be obtained. |
| OPC `RPS15` | Strong regional AD signal and bulk-neocortex eQTL, but no compatible QTL fine-mapping/LD | Same direct recovery path as APOE; this could add a genuinely new gene-level result. |
| Inhibitory `RPS15` | Regional AD signal, but no qualifying neuron eQTL in the tested source | Test larger inhibitory-neuron QTL, pQTL, and alternative AD phenotypes. |
| `COX7C` in astrocyte and inhibitory networks | Regional AD signal, but no qualifying eQTL in either tested source | Test larger cell-specific QTL, pQTL, and unresolved full sQTL data. |
| OPC `ANKRD11` | Regional AD signal, but no qualifying bulk-neocortex eQTL | Test OPC-specific QTL, pQTL, and unresolved full sQTL data. |

For the other 15 nuclear genes, changing the colocalization software cannot
solve the current problem: the Bellenguez diagnosis GWAS has no qualifying
regional signal. They need a larger or differently defined GWAS phenotype, a
gene-based association, or rare-variant association before QTL colocalization
becomes informative.

The six mtDNA genes require a separate mitochondrial association design and
are not valid targets for nuclear cis-eQTL colocalization.

The authoritative route-level evidence is in:

- [`recovery_route_decisions.tsv`](../../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_route_decisions.tsv)
- [`recovery_regional_gwas_summary.tsv`](../../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_regional_gwas_summary.tsv)
- [`recovery_regional_qtl_summary.tsv`](../../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_regional_qtl_summary.tsv)

## Best remaining GWAS/QTL analyses

### 1. Complete the APOE and OPC RPS15 colocalizations

Obtain genotype-derived LD from the actual QTL cohort, an author-generated LD
matrix, or author-generated candidate-specific SuSiE models. Fine-map the GWAS
and eQTL independently and compare their multiple signals with
`coloc.susie`.

This is the cleanest unfinished classical-colocalization analysis. It has high
scientific value for `RPS15`, but low potential gene yield: at most one new
gene-level validation because `APOE` is already genetically established.

Using generic 1000 Genomes LD without demonstrating compatibility would weaken
the result and should not be used merely to force a posterior probability.

### 2. Use newer and larger cell-type-specific brain eQTL panels

Requery all 19 nuclear candidates in large single-nucleus eQTL resources, with
particular attention to:

- astrocytes for `APOE`, `COX7C`, and the other Phase 18 astrocyte candidates;
- OPCs for `RPS15` and `ANKRD11`;
- inhibitory neurons for `RPS15` and `COX7C`; and
- each candidate's other exact Phase 18 broad-network context.

Potential sources include scMetaBrain and the multi-ancestry single-nucleus
human-brain regulatory atlas. The latter contains 5.6 million nuclei from
1,384 donors across eight cell classes and 27 subclasses:

- <https://pubmed.ncbi.nlm.nih.gov/41394650/>
- <https://pmc.ncbi.nlm.nih.gov/articles/PMC11661307/>

Before calling this independent validation, audit whether ROSMAP or Rush donors
contributed to the QTL meta-analysis. Use cohort-specific or
leave-ROSMAP-out results when available. A QTL result that reuses ROSMAP donors
can clarify mechanism but is weaker as independent validation.

This approach cannot help a candidate under the current diagnosis phenotype if
its region still has no GWAS association. The GWAS signal gate must remain
first.

### 3. Run AD-diagnosis GWAS by pQTL colocalization

Test whether AD-associated variants regulate candidate protein abundance in
brain or cerebrospinal fluid, rather than only RNA abundance. This is
particularly relevant to the ribosomal and respiratory-chain candidates,
whose RNA and protein regulation may differ.

A current CSF pQTL atlas contains 3,506 samples and 7,008 measured aptamers.
Public P-value results and FUSION weights are available, while full statistics
may require an application. The publication also points to public GWAS Catalog
files:

- <https://www.nature.com/articles/s41588-024-01972-8>
- <https://dss.niagads.org/datasets/ng00130/>

The first step must be a coverage inventory: determine which of the 19 nuclear
candidate proteins were measured reliably and have a cis-pQTL. Only cis-pQTLs
should be primary instruments; trans-pQTLs are more vulnerable to pleiotropy
and should be secondary.

This route has strong biological interpretability but, when paired with the
same Bellenguez diagnosis GWAS, remains limited mainly to the four regions that
already contain an AD signal.

### 4. Use quantitative AD endophenotype GWAS

Replace broad AD case-control diagnosis with quantitative traits closer to AD
pathology, including:

- CSF A-beta 42;
- CSF total tau;
- CSF p-tau181;
- amyloid or tau PET burden;
- neuropathology burden;
- cognitive decline or age at onset; and
- resilience despite pathology.

The strongest immediately actionable source is the 2026 CSF biomarker
meta-analysis of 18,948 people of European ancestry. It identified 12
genome-wide-significant loci across the three biomarkers, eight reported as
novel. Full summary statistics are publicly registered as:

| Trait | Public source |
|---|---|
| A-beta 42 | GWAS Catalog series containing `GCST90726396` |
| Total tau | GWAS Catalog series containing `GCST90726397` |
| p-tau181 | GWAS Catalog series containing `GCST90726398` |

The files are also registered under NIAGADS `NG00191` and linked directly from
the paper's data-availability section:

- <https://www.nature.com/articles/s41467-026-71682-8>
- <https://dss.niagads.org/datasets/ng00191/>

Endophenotypes may uncover candidate-region signals hidden by clinical
heterogeneity or presymptomatic controls in a diagnosis GWAS. They also narrow
interpretation: a shared p-tau signal points to tau-related genetic biology,
not automatically to all AD risk.

### 5. Run sex- and APOE-stratified GWAS/QTL analyses

Phase 18 candidates were frequently supported in particular sex/APOE strata,
whereas the completed Bellenguez analysis is an overall GWAS. The most matched
genetic design would test:

- SNP-by-sex interaction;
- SNP-by-APOE interaction;
- prespecified sex-specific GWAS;
- prespecified APOE-genotype-specific GWAS; and
- matching sex/APOE interaction eQTLs or pQTLs.

Formal interaction tests are preferable to claiming an interaction because one
subgroup is significant and another is not. This route has excellent context
match but poor immediate feasibility: subgroup sample sizes fall quickly,
individual-level controlled data are usually necessary, and conditioning on
APOE requires special care in chromosome 19 analyses.

### 6. Run candidate-frozen MAGMA, TWAS, and PWAS

Use the independently selected Phase 18 candidate set to perform:

- MAGMA gene-based association for the 19 nuclear genes;
- FUSION or S-PrediXcan TWAS using multiple brain-expression models;
- PWAS using brain and CSF protein models; and
- conditional TWAS/PWAS and FOCUS-style fine-mapping.

These methods aggregate information across multiple variants and can detect a
gene association even when no single variant is genome-wide significant. They
are therefore useful screens for the 15 currently signal-negative regions.

They do not prove colocalization. LD hitchhiking, correlated prediction models,
and effects on neighboring genes can produce significant results. A TWAS or
PWAS result should be graded as suggestive unless it replicates across
independent models/cohorts and is supported by colocalization or fine-mapped
high inclusion probability.

### 7. Perform rare-variant gene-burden association

Test prespecified loss-of-function, damaging missense, and splice masks for the
19 nuclear candidates using burden tests and SKAT-O. Analyze ancestries
separately and meta-analyze only after ancestry-specific QC. Require an
independent replication cohort or a consistent mask-level replication.

ADSP Release 5 contains 58,507 whole genomes and has demonstrated gene-based
rare-variant discovery:

- <https://pmc.ncbi.nlm.nih.gov/articles/PMC13060494/>
- <https://dss.niagads.org/datasets/ng00067/>

This route can implicate genes that lack common-variant GWAS signals and is
scientifically strong. It is not the recommended immediate local task because
custom analysis requires controlled individual-level data and much larger
storage and computation than the summary-statistic routes.

### 8. Run a dedicated mtDNA association analysis

For `MT-ATP6`, `MT-CO2`, `MT-CO3`, `MT-CYB`, `MT-ND4`, and `MT-ND5`, evaluate:

- homoplasmic variants;
- heteroplasmy;
- mitochondrial haplogroup;
- mtDNA copy number; and
- associations with AD diagnosis and quantitative biomarkers.

ADSP WGS can support mtDNA variant calling, and MitoH3 was developed for
homoplasmic, heteroplasmic, and haplogroup analysis in ADSP:

- <https://pubmed.ncbi.nlm.nih.gov/38746629/>

This is necessary to address the six genes that nuclear GWAS/QTL cannot
evaluate, but it should be a separate workstream because its variants,
inheritance, QC, and association models differ substantially from nuclear
cis-QTL analysis.

## Comparative evaluation

The options were evaluated for scientific strength, potential to add supported
genes, immediate data availability, local feasibility, and match to the Phase
18 context.

| Approach | Scientific strength if successful | Potential to add genes | Data/local feasibility now | Principal limitation | Priority |
|---|---|---|---|---|---:|
| CSF endophenotype GWAS, then gated QTL colocalization | High and mechanism-specific | Medium-high across all 19 nuclear genes | High; three full public GWAS files and local summary-statistic analysis | A positive result is biomarker-specific; LD/QTL compatibility is still required after the GWAS gate | **1** |
| CSF/brain pQTL inventory and AD colocalization | High | Medium, but initially constrained to diagnosis-GWAS signal regions | Medium-high; public coverage/results, some full files require access | Protein may be unmeasured; cis-pQTL and overlap audits required | **2** |
| Complete APOE and OPC RPS15 colocalization | Very high for the exact shared-signal question | Low; at most RPS15 is a new gene result | Low-medium; blocked on source-matched QTL LD/model | External coordination and only two routes | **3** |
| New cell-type-specific eQTL/sQTL | High with exact context and compatible models | Low-medium under the existing diagnosis GWAS | Medium | No GWAS signal for most genes; possible ROSMAP donor overlap | **4** |
| Candidate MAGMA/TWAS/PWAS | Moderate without colocalization; high as a discovery screen | High screening yield | High and local | Significant prediction is not necessarily causal gene assignment | **Parallel supporting analysis** |
| Rare-variant burden/SKAT-O | High with replicated masks | High theoretical reach | Low locally | Controlled 58K WGS, storage, compute, ancestry and mask complexity | **Later controlled-data phase** |
| Sex/APOE interaction GWAS/QTL | High context relevance | Uncertain | Low | Severe power loss and need for individual-level data | **Later targeted phase** |
| mtDNA association | High for the six mtDNA genes | Restricted to six mtDNA genes | Low-medium | Separate controlled WGS and mitochondrial QC workflow | **Separate parallel plan** |

## Recommended next workstream

### Name

**Phase 19 endophenotype GWAS/QTL extension**

### Primary question

Do any of the 19 nuclear Phase 18 candidates have a corrected regional or
gene-based association with CSF A-beta 42, total tau, or p-tau181, and, where a
signal exists, does it share a fine-mapped causal signal with a candidate
eQTL, sQTL, or pQTL?

### Ordered analysis

1. Freeze the same 19 nuclear genes, 27 nuclear candidate contexts, genome
   build, candidate windows, and grade definitions before opening results.
2. Acquire and checksum the three public 2026 CSF biomarker GWAS summary files.
3. Audit sample ancestry, genome build, alleles, effect scale, sample size,
   variant coverage, and any cohort overlap with planned QTL sources.
4. Extract all 19 candidate regions without applying a result-favorable filter.
5. Run two prespecified GWAS gates:
   - primary regional single-variant gate: `P < 5e-8`;
   - secondary candidate-frozen gene-based gate with correction across all
     tested genes and three biomarkers.
6. Use the gates for different purposes:
   - a pair passing the regional single-variant gate may enter regional
     fine-mapping and classical colocalization;
   - a pair passing only the gene-based gate may enter conditional MAGMA,
     TWAS, or PWAS follow-up, but not H0-H4 colocalization unless an independent
     regional signal model is established; and
   - a pair failing both gates receives a terminal no-signal status without LD
     or QTL-model acquisition.
7. For pairs eligible for regional colocalization, inventory QTL evidence in
   this order:
   - cis-CSF or brain pQTL;
   - exact-cell-type brain eQTL;
   - exact or defensible fallback sQTL;
   - bulk-brain eQTL only as fallback.
8. Require full regional QTL statistics or a released fine-mapping model and
   compatible ancestry-matched LD before classical H0-H4 analysis.
9. Use multi-signal fine-mapping and `coloc.susie` where LD permits; do not
   downgrade to a convenient one-signal result merely to obtain H4.
10. Audit participant overlap between the biomarker GWAS and QTL study. Use an
    independent QTL source or leave-overlap-out statistics where possible.
11. Report separate grades for A-beta, total tau, and p-tau181. Do not merge
    them into general AD support without an explicit rule.
12. Preserve `none_found` versus `not_assessable`, and publish a complete
    candidate-by-biomarker matrix even if no candidate passes.

### Why this precedes the two-route APOE/RPS15 recovery

Completing APOE and RPS15 remains worthwhile, but it should not be the next
main workstream when the stated goal is to validate more Phase 18 genes:

- APOE is already strongly established;
- only RPS15 could become a newly supported gene;
- progress depends on external QTL-cohort LD or author-generated models; and
- the work does not address the 15 nuclear genes lacking a diagnosis-GWAS
  regional signal.

The endophenotype screen tests all 19 nuclear genes with open data and creates
new legitimate signal opportunities. APOE/RPS15 author outreach can proceed in
parallel without blocking the local analysis.

### Local execution decision

The recommended endophenotype GWAS screening, regional extraction,
candidate-set MAGMA, source inventory, and gate evaluation can all run locally.
Minerva is not required. Results can remain under a new validated directory in
`results/minerva_production/`.

Only candidate-biomarker routes passing the upstream gates should trigger
larger QTL/LD downloads. ADSP individual-level rare-variant, sex/APOE
interaction, and mtDNA analyses are not realistically local summary-statistic
tasks and should remain separately scoped.

## Success criteria

The next workstream is successful scientifically even if it adds zero genes,
provided that:

- all 19 nuclear genes and all three biomarkers are assessed under frozen
  rules;
- source integrity, alleles, ancestry, coverage, and overlap are audited;
- every candidate-biomarker pair has a terminal status;
- QTL colocalization is attempted only after valid regional single-variant
  GWAS and QTL signal gates;
- shared versus distinct signals are modeled with compatible LD;
- biomarker-specific conclusions are not overstated as general AD causality;
  and
- the output distinguishes negative evidence from unavailable or incompatible
  data.

The number of newly supported genes is an outcome, not a completion criterion.
