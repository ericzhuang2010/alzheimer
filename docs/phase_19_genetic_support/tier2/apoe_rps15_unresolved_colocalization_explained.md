# Why the APOE and RPS15 GWAS/eQTL results remain unresolved

## Short answer

For both `APOE` and the OPC `RPS15` comparison, Phase 19 found two real
statistical signals in the same genomic region:

1. nearby DNA variants are associated with Alzheimer disease in the GWAS; and
2. nearby DNA variants are associated with the amount of RNA produced by the
   candidate gene in bulk neocortex.

That is promising, but it does not show that the same causal DNA variant
produces both effects. The released QTL data did not include the fine-mapped
model or the study-matched linkage disequilibrium information needed to answer
that question reliably. Consequently, these routes are **unresolved**, not
positive and not negative colocalizations.

For `APOE`, this limitation does not challenge the extensive independent
evidence that APOE is an AD gene. It limits a much narrower claim: whether the
regional AD association operates through genetically regulated APOE expression
in a context relevant to the Phase 18 astrocyte network. For `RPS15`, the
limitation is more consequential because the regional GWAS association cannot
yet be assigned to regulation of `RPS15`.

## A plain-language analogy

Imagine that two alarms sound in the same neighborhood:

- a hospital reports an unusual cluster of illness; and
- an environmental sensor reports unusual smoke.

The observations could have the same cause, such as one nearby fire. They could
also come from two different events that happen to be close together. Knowing
only that both alarms occurred in the same neighborhood is not enough to
decide.

In this analogy:

- the AD GWAS signal is the illness alarm;
- the eQTL signal is the smoke alarm;
- individual variants are possible addresses;
- linkage disequilibrium, or LD, tells us which addresses are so closely linked
  that their signals are difficult to distinguish; and
- fine-mapping estimates which address or small group of addresses is most
  likely to contain the actual source.

Colocalization asks whether the two alarms most likely trace back to the same
address.

## What the important terms mean

| Term | Meaning in this analysis |
|---|---|
| GWAS | A study testing whether inherited DNA variants are more common in people with AD than in controls. |
| Regional GWAS signal | At least one variant in the candidate's prespecified genomic window is strongly associated with AD. It does not by itself identify the responsible gene. |
| eQTL | A DNA variant associated with the measured expression level of a gene. |
| cis-eQTL | An eQTL located near the gene whose expression it affects. Phase 19 examined this local form of regulation. |
| LD | Correlation between nearby variants because they tend to be inherited together. LD patterns vary with ancestry and study population. |
| Fine-mapping | A statistical analysis that separates correlated variants and assigns probabilities to possible causal variants or credible sets. |
| Colocalization | A statistical comparison asking whether the GWAS and QTL signals are best explained by the same causal variant. |
| Bulk-brain fallback | QTL evidence measured in mixed neocortical tissue rather than the exact Phase 18 cell type. |

## What "bulk neocortex" means

Yes, bulk neocortex is a type of biological dataset and describes both the
source tissue and how it was measured.

The **neocortex** is the outer part of the cerebral cortex. The **bulk** part
means that a piece of neocortical tissue was processed as one mixed sample.
RNA was measured from all cells in that piece of tissue together rather than
separating the cells and measuring astrocytes, OPCs, neurons, or other cell
types individually.

A bulk-neocortex sample can therefore contain RNA from:

- excitatory and inhibitory neurons;
- astrocytes;
- oligodendrocytes and OPCs;
- microglia and other immune cells; and
- endothelial, perivascular, and other vascular cells.

The QTL study combined two kinds of information across donors:

1. each donor's inherited DNA variants; and
2. the amount of RNA measured for each gene in that donor's mixed neocortical
   tissue.

It then tested whether donors carrying a particular variant tended to have
more or less RNA from a gene. That variant-gene association is an eQTL. The
Phase 19 bulk-neocortex source had 211 samples.

This is useful brain-relevant evidence, but it cannot identify which cell type
produced the association. For example, an `APOE` bulk-neocortex eQTL might be
driven primarily by astrocytes, another glial population, differences in cell
composition, or a mixture of effects. Similarly, the `RPS15` result cannot be
assumed to be an OPC eQTL.

That is why Phase 19 labels these results as **bulk-brain fallback**:

- bulk neocortex is more relevant than a non-brain tissue;
- it can support a general brain regulatory hypothesis; but
- it does not validate the exact Phase 18 astrocyte or OPC context.

An exact-context follow-up would use a sufficiently powered astrocyte-specific
eQTL dataset for the Phase 18 `APOE` comparison and an OPC-specific eQTL
dataset for the Phase 18 `RPS15` comparison.


## What Phase 19 actually found

The AD statistics came from the full Bellenguez 2022 case-control GWAS. The
QTL statistics came from a released neocortex eQTL study with 211 samples. The
regional data were dense enough to establish that both traits had signals, but
the released QTL fine-mapping files did not contain models for these target
genes.

| Phase 18 comparison | AD GWAS result | Neocortex eQTL result | Context match | Terminal result |
|---|---|---|---|---|
| Astrocyte `APOE` | Extremely strong regional AD association; the stored minimum P value underflowed to zero in the source representation | Minimum P = `9.51257e-8`, passing the frozen per-gene threshold of `4.33952e-6` | Bulk-neocortex fallback, not an exact astrocyte eQTL | `model_or_ld_incompatible` |
| OPC `RPS15` | Regional minimum P = `4.089e-30` | Minimum P = `2.11971e-6`, passing the frozen per-gene threshold of `3.75883e-6` | Bulk-neocortex fallback, not an exact OPC eQTL | `model_or_ld_incompatible` |

The eQTL P values answer only, "Is some nearby variant associated with this
gene's expression?" They do not answer, "Is the AD-associated variant the same
variant?"

The detailed values are recorded in:

- [`recovery_regional_gwas_summary.tsv`](../../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_regional_gwas_summary.tsv)
- [`recovery_regional_qtl_summary.tsv`](../../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_regional_qtl_summary.tsv)
- [`recovery_route_decisions.tsv`](../../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_route_decisions.tsv)

## Why two signals in the same region are not enough

Suppose variants A and B are located close together and are usually inherited
together. The GWAS might show a strong association at both variants even if
only A influences AD. The eQTL study might also show associations at both even
if only B influences gene expression. Looking only at P values could make the
two traits appear to share a cause when the true causal variants are different.

There are therefore at least two possible explanations:

1. **Shared causal signal:** one variant changes candidate-gene expression and
   that regulatory change affects AD risk.
2. **Distinct linked signals:** one variant affects AD and a different,
   correlated variant affects candidate-gene expression.

Only the first explanation provides the desired regulatory genetic support for
the candidate. LD-aware fine-mapping and colocalization are needed to
distinguish them.

## Why a shared causal signal matters

We do not need to demonstrate a shared signal for every possible kind of gene
validation. We need it specifically if we want to claim that the GWAS supports
the candidate gene through genetically regulated expression.

A GWAS usually identifies a genomic region, not automatically the responsible
gene. A region can contain many variants, genes, and regulatory elements.
Consider two nearby variants:

- variant A increases AD risk but acts through another gene or mechanism; and
- variant B changes `RPS15` expression but has no effect on AD.

If A and B are inherited together because of LD, the regional GWAS and eQTL
plots can look similar even though `RPS15` expression is unrelated to the AD
association. In that situation, the evidence would show only that an AD signal
and an `RPS15` eQTL occupy the same neighborhood.

If valid colocalization instead supports one shared causal signal, the results
become consistent with the proposed chain:

> DNA variant -> altered candidate-gene expression -> altered AD risk

This makes the GWAS relevant to the candidate rather than merely relevant to
its genomic neighborhood.

Colocalization still does not fully prove that expression mediates the disease
effect. A shared variant could independently affect candidate-gene expression
and affect AD through another gene or biological mechanism. Stronger mediation
claims can require additional evidence such as cis-instrument Mendelian
randomization, molecular mediation analysis, perturbation experiments, and
independent replication. Colocalization is therefore strong genetic support
for a shared signal, not final proof of the entire causal chain.

This distinction has different consequences for the two genes:

- For `APOE`, shared-signal colocalization is not needed to establish APOE as
  an AD gene because independent coding-variant and other genetic evidence is
  already strong. It would clarify whether genetically regulated APOE RNA
  abundance is part of the mechanism in the tested tissue.
- For `RPS15`, the distinction is essential. Without a shared signal, the data
  show only that an AD locus is near `RPS15` and that `RPS15` has an eQTL. They
  do not show that the AD locus acts through `RPS15`.

Accordingly, a shared signal is required to call this result **GWAS-eQTL
genetic support for the candidate gene**, but it is not required for every
other form of candidate validation.


## What was missing

### 1. A released QTL fine-mapping model

The source advertised SuSiE fine-mapping releases, but its released model files
contained no model rows or credible sets for the `APOE` and `RPS15` target
traits. Dense association statistics were available, but association
statistics are not a substitute for the fitted multi-signal model.

A SuSiE model is especially helpful because a region can contain more than one
independent causal signal. Treating a complex region as if it contains only one
causal variant can give an incorrect colocalization result.

### 2. LD appropriate for the QTL cohort

To fit the missing QTL model ourselves, we need to know the correlations among
the tested variants in the people who contributed the QTL data. Ideally this is
calculated directly from their genotypes. A carefully ancestry-matched panel
can sometimes be used as a fallback, but it is weaker than in-study LD.

An LD panel for the AD GWAS side cannot replace QTL-study LD. The two studies
have different participants and may have different ancestry composition,
variant frequencies, imputation, and quality-control filters.

### 3. Fully compatible variant representation

The two signal models must refer to the same genome build and ordered variants,
with aligned reference and effect alleles. Strand-ambiguous variants and allele
frequency discrepancies must be resolved before the models can be compared.

## Why Phase 19 did not simply use 1000 Genomes LD

LD is not a universal property of a chromosome. It depends on population
history and therefore differs across ancestry groups. It can also differ
because of sample size, imputation, and variant filtering.

Using a convenient but mismatched reference panel can:

- combine two distinct signals incorrectly;
- split one shared signal incorrectly;
- change which variants enter a credible set; and
- produce an apparently precise posterior probability that is scientifically
  misleading.

The pipeline therefore stopped at `model_or_ld_incompatible` instead of
forcing an answer from unsuitable inputs. This was a scientific safeguard, not
a software failure.

## What a completed colocalization would report

Classical colocalization compares five broad explanations:

| Hypothesis | Interpretation |
|---|---|
| H0 | Neither trait has a regional association. |
| H1 | Only AD has a regional association. |
| H2 | Only gene expression has a regional association. |
| H3 | Both have associations, but different causal variants explain them. |
| H4 | Both have associations and share a causal variant. |

For these two routes, the observed signals make H3 versus H4 the key
scientific question. Phase 19 did not calculate their posterior probabilities
because the required compatible models were unavailable.

A high, robust H4 posterior would support a shared genetic signal. A high H3
posterior would indicate that the AD and expression signals are probably
distinct. An indecisive posterior would leave the route unresolved.

## What a future positive result would and would not prove

If a valid analysis strongly favored H4, it would support the statement:

> The AD association and genetically regulated expression of this gene appear
> to share a causal signal in the tested neocortex QTL dataset.

It would not, by itself, prove that:

- the gene is the only functional gene at the locus;
- altered expression causes every aspect of AD;
- the Phase 18 network direction is causal;
- the effect occurs specifically in astrocytes or OPCs; or
- changing the gene would be safe or beneficial therapeutically.

The last two limitations matter because both available eQTL signals came from
bulk neocortex. A bulk sample mixes neurons, glia, and vascular cells.

## Gene-specific interpretation

### APOE

Human genetics already strongly establishes `APOE` as an AD-relevant gene,
including direct coding-variant evidence. The unresolved colocalization does
not reduce that established gene-level conclusion.

Instead, it leaves open a narrower mechanism: whether a regional AD signal is
shared with genetically regulated APOE RNA abundance in bulk neocortex. Even a
positive result would provide only fallback support for the Phase 18 astrocyte
context until an astrocyte-specific QTL analysis reproduced it.

### RPS15

For OPC `RPS15`, the result is a promising lead but not a gene assignment. The
region contains a strong AD association and bulk neocortex contains a
significant `RPS15` eQTL, but those observations may be driven by distinct
linked variants. Until H3 and H4 can be compared with compatible models, the AD
locus cannot be attributed to `RPS15` regulation.

An exact OPC eQTL would also be preferable to the current bulk-neocortex
fallback. A successful bulk result followed by an OPC-specific replication
would provide a substantially stronger connection to the Phase 18 finding.

## What is needed to resolve the routes

The cleanest future analysis would:

1. obtain individual-level genotypes from the QTL study or an author-generated
   LD matrix for the exact analyzed samples;
2. retain complete dense QTL effect estimates, standard errors, alleles,
   frequencies, and sample size;
3. obtain ancestry-compatible LD for the GWAS side;
4. harmonize genome build, variants, alleles, and ordering;
5. fine-map the GWAS and QTL independently with a multi-signal method such as
   SuSiE;
6. compare matched signals using `coloc.susie`;
7. test sensitivity to priors, LD choice, variant inclusion, and conditional
   signals; and
8. seek replication using an independent, preferably cell-type-specific QTL
   cohort.

If the original QTL cohort cannot release genotypes, an author-provided LD
matrix and fitted SuSiE output would be sufficient for the main comparison and
would avoid transferring individual-level data.

## Wording to use now

Recommended wording:

> APOE and OPC RPS15 each had both a regional AD association and a bulk-neocortex
> eQTL signal. Classical colocalization remained unresolved because the released
> source omitted candidate-specific QTL fine-mapping models and compatible QTL
> LD. These results are promising signal coverage, not evidence that the AD and
> expression associations share a causal variant.

Avoid wording such as:

- "APOE/RPS15 colocalized with AD";
- "the eQTL explains the AD association";
- "RPS15 is the causal gene at the locus"; or
- "failure to calculate H4 disproves the gene."

The complete recovery outcome is documented in the
[`tier2_recovery_execution_report.md`](tier2_recovery_execution_report.md).
