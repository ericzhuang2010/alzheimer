# Phase 19 Tier 1 human genetic support: what we did and how we reached the conclusion

## Executive summary

Phase 18 identified 25 candidate key-driver genes in 47 gene × broad-cell-type
contexts. Phase 19 Tier 1 asked a separate question:

> Does existing human genetic evidence support any of these candidate genes in
> Alzheimer disease, and does the evidence fit the cell-type/network context in
> which Phase 18 identified the gene?

We answered this by screening an official, public, summary-level Alzheimer
disease GWAS/fine-mapping/xQTL resource. We did **not** download individual
genotypes, rerun a GWAS, or test the Phase 18 expression data again.

The Tier 1 conclusion is:

- **APOE has strong gene-level AD genetic support**, but the functional QTL
  evidence available in Tier 1 is from fallback brain contexts rather than an
  exact astrocyte result. Therefore, this supports APOE as an AD-relevant gene,
  but it does not prove that the Phase 18 astrocyte network mechanism is causal.
- **COX7C has weak/suggestive support** in both of its Phase 18 contexts. The
  same bulk-brain sQTL result is applied to the astrocyte and inhibitory-neuron
  contexts; these are not two independent genetic replications.
- **SELENOW has weak support** because it appears in the release's TWAS gene
  list, but the public companion table lacks the model statistic and exact
  excitatory-neuron context needed for stronger interpretation.
- For **16 other nuclear genes**, no direct gene mapping was found in the
  registered filtered Tier 1 source. This means “not found in this screen,” not
  “genetic evidence is absent.”
- The **six mtDNA genes** could not be evaluated with this nuclear GWAS/xQTL
  source. They need mtDNA-specific association data and were labeled “not
  assessable,” not negative.

Across the 47 Phase 18 candidate-context units, this produced one strong, zero
moderate, three weak, 23 none-found-in-source, and 20 not-assessable results.

## A lay explanation of the analysis

Phase 18 used brain molecular networks to identify genes that look important
inside disease-related cell networks. That is similar to finding people who
occupy central positions in a communication network.

Phase 19 asked whether an entirely different kind of evidence points to the
same people: inherited DNA differences in human populations. Agreement between
the network analysis and human genetics is valuable because the two approaches
have different weaknesses.

The important distinction is between a variant being **near** a gene and a
variant being credibly **connected to** that gene:

- A nearby variant is like an event occurring in the same neighborhood. It
  does not identify which resident caused or experienced the event.
- Fine-mapping narrows the variants that may drive a genetic association.
- xQTL evidence asks whether a variant changes gene expression, splicing,
  protein level, or another molecular trait.
- Colocalization asks whether the AD association and molecular-trait
  association appear to arise from the same underlying genetic signal.
- Cell-type matching asks whether that molecular evidence was observed in the
  same broad cell type as the Phase 18 network result.

We therefore did not count every AD-associated variant within one megabase of
a candidate as evidence for that candidate. Nearby-only records were retained
for audit and locus review, but they did not earn a positive gene grade.

## Starting point: how the 25 genes and 47 contexts were recovered

The candidate list was rebuilt directly from the canonical Phase 18 result:

```text
results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv
```

The prespecified selection rule was:

1. retain rows with `top5_display = TRUE`;
2. identify the gene from `key_driver`;
3. preserve its `broad_network` and `case_id`; and
4. deduplicate on `key_driver + broad_network + case_id`.

This reproduced exactly 47 candidate-context units and 25 unique genes. No
candidate was added or removed after looking at the genetics results.

The Phase 18 input was protected by the frozen SHA-256 checksum:

```text
b917f70e6edcdf030f63e88ba8fbc5b22b80714599c12c80ea449e8c38bd51d8
```

This matters because it prevents a subtle form of selection bias: changing the
candidate list after discovering which genes have favorable genetic evidence.

## New data obtained for Tier 1

We acquired approximately 8.8 MiB of public summary files from the official
[FunGen-xQTL resource repository](https://github.com/statfungen/xqtl-resources)
at commit:

```text
f6f63fc319a417213cf1e86ec0eb14fcb53d2427
```

The six source files contained:

- a unified AD locus and xQTL workbook;
- a variant-level AD fine-mapping/colocalization table;
- an AD gene/variant-coding plus xQTL companion gene list;
- an AD TWAS/GVC/xQTL companion gene list;
- molecular-context metadata; and
- the source's Synapse folder/resource map.

We also used existing, frozen local references:

- GENCODE v44 basic annotation on GRCh38 for gene coordinates; and
- the HGNC 2026-06-05 table for approved gene symbols.

No participant-level genotype, phenotype, BAM/CRAM, or VCF data were obtained.
The downloaded files, sizes, source version, and checksums are recorded in:

```text
data/reference/phase19_genetic_support/source_manifest.tsv
```

## Analysis workflow

### 1. Freeze the scope and interpretation rules

Before extracting candidate-specific results, the configuration fixed:

- the Phase 18 input and checksum;
- the expected 25 genes and 47 candidate-context units;
- GRCh38 as the genome build;
- a ±1 Mb candidate-gene window;
- broad-network to xQTL-context mappings;
- allowed evidence routes;
- grade definitions; and
- rules for `none_found` and `not_assessable`.

This is an evidence-synthesis screen, not a newly fitted association model. We
did not choose among alternative statistical tests after viewing the results.

### 2. Resolve every candidate gene and locus

All 25 symbols were checked against HGNC. Each gene was mapped to a GENCODE v44
GRCh38 coordinate, strand, transcription start site, and ±1 Mb locus. The six
mtDNA genes were flagged before the genetics evidence was reviewed so that
nuclear-LD logic would not be incorrectly applied to mitochondrial variants.

### 3. Screen the AD variant table around each nuclear gene

For each of the 19 nuclear genes, the workflow extracted source variants inside
the frozen ±1 Mb window. This yielded 356 variant-based records plus one TWAS
gene-list record:

- 352 regional variants with proximity only;
- four direct xQTL target records: three for APOE and one for COX7C; and
- one direct TWAS-list record for SELENOW.

The 352 proximity-only variants were retained in the detailed table and locus
plots, but they did not increase a candidate's support grade. This guard is
central to the conclusion: an AD locus can contain many genes, and physical
distance alone does not identify the relevant gene.

### 4. Extract precomputed functional and colocalization evidence

The unified workbook yielded eight candidate-gene colocalization-related
records:

- seven APOE records; and
- one COX7C record.

The source reports quantities such as inclusion score, VCP, confidence level,
and CL1-CL6. We preserved these names and meanings. We did not rename them as
classical coloc `PP.H4`.

The public snapshot did not contain the H0-H4 posterior set or complete dense
regional inputs needed to calculate it ourselves. Consequently:

- all H0-H4 fields are explicitly missing;
- the QC table says `summary_available_no_h0_h4` where a filtered result was
  available; and
- no classical PP.H4 claim is made.

### 5. Check TWAS and gene/variant-coding companion lists

The companion gene lists were searched for every candidate:

- SELENOW appeared in the TWAS list.
- APOE appeared in both the TWAS list and the ADSP GVC-related list.
- COX7C appeared through the xQTL/ColocBoost route.

These lists are useful for screening but do not all provide a full test
statistic. For example, APOE's GVC membership did not include a burden-test
effect, mask, allele-frequency threshold, P value, multiplicity correction, or
replication result. It was therefore recorded as reported membership, not as a
positive rare-variant burden test.

### 6. Assess cell-type/context agreement

Each Phase 18 broad network was mapped to the closest prespecified xQTL context:

| Phase 18 broad network | Requested xQTL context |
|---|---|
| Astrocytes | Ast |
| Excitatory neurons | Exc |
| Inhibitory neurons | Inh |
| Microglia | Mic |
| OPCs | OPC |
| Oligodendrocytes | Oli |
| Vasculature cells | Brain fallback |

An exact context match would strengthen a mechanistic interpretation. A bulk
brain or other-cell-type result can support the gene more generally, but it
does not validate the exact Phase 18 cell network.

None of the positive Tier 1 findings supplied a complete, exact-context,
classical colocalization result. The final wording therefore separates
gene-level support from context-specific support.

### 7. Assign a terminal grade to every candidate-context unit

The frozen grades mean:

| Grade | Operational meaning |
|---|---|
| Strong | A direct candidate mapping with a genome-wide AD signal and high-inclusion or coding evidence. |
| Moderate | A direct candidate mapping with replication or strong precomputed functional support. |
| Weak | A direct candidate mapping exists, but the AD signal, context, replication, or available statistics are limited. |
| None found | The registered, filtered Tier 1 source was searched but contained no direct mapping to the candidate. This is not evidence of absence. |
| Not assessable | The route requires data not present in the registered source. |

These grades are descriptive evidence categories, not probabilities that a
gene is causal.

## How the positive conclusions were reached

### APOE: strong gene-level support, fallback context

The source contains the APOE variant rs429358 with:

- a minimum reported AD GWAS P value of approximately `1.88 × 10^-155`;
- AD fine-mapping inclusion score `1.0`;
- direct mapping to APOE; and
- a known protein-changing APOE variant consequence.

This satisfies the frozen strong gene-level rule. However, the functional
context in the Tier 1 source was a fallback brain context, not a complete
astrocyte-specific H0-H4 colocalization. The permitted conclusion is therefore:

> Human genetics strongly supports APOE as an AD-relevant gene, and this is
> consistent with the Phase 18 APOE result. Tier 1 does not establish that the
> genetic effect operates through the specific astrocyte network identified by
> Phase 18.

### COX7C: weak, context-mismatched support

The direct COX7C record was rs2010322 and reported:

- minimum AD GWAS P value approximately `2.64 × 10^-6`;
- AD inclusion score approximately `0.0023`;
- xQTL inclusion score approximately `0.026`;
- bulk sQTL context `ROSMAP_AC_sQTL`; and
- source confidence category `CL5`.

The AD association is below conventional genome-wide significance, the
inclusion scores are low, and the source context is bulk rather than exact
astrocyte or inhibitory-neuron evidence. It therefore receives a weak grade in
both Phase 18 contexts.

The two weak rows represent the same underlying genetic evidence projected onto
two Phase 18 contexts. They must not be described as independent replication.

**Validation-panel implication.** COX7C should be added to the first
labor-intensive validation panel in both of its displayed broad networks:
astrocytes and inhibitory neurons. It is useful precisely because it connects a
recurrent nuclear complex-IV KDA candidate to the only non-APOE direct xQTL
target record in this Tier 1 screen. Its priority is a reason to test the
network and protein mechanism, not permission to upgrade the weak genetic
grade. Each gene × network unit must be assessed separately.

### SELENOW: weak TWAS-list support

SELENOW appears in the release's TWAS companion gene list. This is a direct
gene-level flag, so it is more informative than proximity alone. However, the
public list does not provide the model-level statistic, multiplicity-adjusted
result, direction, or exact excitatory-neuron context needed to confirm and
interpret the signal. It therefore receives a weak, explicitly limited grade.

## Results for all 25 genes

| Gene | Phase 18 broad network(s) | Tier 1 grade | Interpretation |
|---|---|---|---|
| ANKRD11 | OPCs | None found | No direct mapping in the registered filtered source. |
| APOE | Astrocytes | Strong | Strong gene-level AD support; functional context is fallback rather than exact astrocyte evidence. |
| ATP6V1F | Inhibitory neurons | None found | No direct mapping in the registered filtered source. |
| COX4I1 | Astrocytes; excitatory neurons | None found | No direct mapping in the registered filtered source. |
| COX6B1 | Excitatory neurons | None found | No direct mapping in the registered filtered source. |
| COX7C | Astrocytes; inhibitory neurons | Weak | One bulk sQTL/AD CL5 result; sub-genome-wide and not an exact cell-type match. |
| DYNLT1 | Excitatory neurons | None found | No direct mapping in the registered filtered source. |
| FTL | OPCs | None found | No direct mapping in the registered filtered source. |
| LAMTOR5 | Excitatory neurons; inhibitory neurons | None found | No direct mapping in the registered filtered source. |
| LAPTM4A | Astrocytes | None found | No direct mapping in the registered filtered source. |
| MT-ATP6 | Astrocytes; vasculature cells | Not assessable | mtDNA-specific association source absent. |
| MT-CO2 | Astrocytes; excitatory neurons; inhibitory neurons; microglia; OPCs; oligodendrocytes; vasculature cells | Not assessable | mtDNA-specific association source absent. |
| MT-CO3 | Astrocytes; inhibitory neurons; OPCs; vasculature cells | Not assessable | mtDNA-specific association source absent. |
| MT-CYB | Excitatory neurons; inhibitory neurons | Not assessable | mtDNA-specific association source absent. |
| MT-ND4 | Microglia; OPCs; oligodendrocytes; vasculature cells | Not assessable | mtDNA-specific association source absent. |
| MT-ND5 | Inhibitory neurons | Not assessable | mtDNA-specific association source absent. |
| NCOA1 | OPCs | None found | No direct mapping in the registered filtered source. |
| RPL11 | Astrocytes; excitatory neurons; microglia; oligodendrocytes | None found | No direct mapping in the registered filtered source. |
| RPL15 | Astrocytes | None found | No direct mapping in the registered filtered source. |
| RPL38 | Inhibitory neurons | None found | No direct mapping in the registered filtered source. |
| RPLP1 | Astrocytes; inhibitory neurons | None found | No direct mapping in the registered filtered source. |
| RPS13 | Excitatory neurons | None found | No direct mapping in the registered filtered source. |
| RPS15 | Inhibitory neurons; OPCs | None found | No direct mapping in the registered filtered source. |
| SELENOW | Excitatory neurons | Weak | Present in TWAS gene list; detailed statistic and exact context unavailable. |
| UQCR10 | Excitatory neurons | None found | No direct mapping in the registered filtered source. |

## What “none found” means

The public workbook is a filtered, integrated resource. If a gene does not
appear as a direct target, we know only that the registered summary did not
report a qualifying direct mapping for it.

We do **not** know that:

- the gene has no inherited contribution to AD;
- a different ancestry or phenotype would be negative;
- a rare-variant study would be negative;
- another brain region or disease stage would be negative;
- a trans-regulatory mechanism is absent; or
- the Phase 18 network result is biologically incorrect.

Accordingly, “none found” is a search outcome, not a null-hypothesis result. No
equivalence test or Bayesian evidence-for-the-null analysis was possible from
this filtered table.

## Why the mtDNA genes are “not assessable”

MT-ATP6, MT-CO2, MT-CO3, MT-CYB, MT-ND4, and MT-ND5 are encoded by the
mitochondrial genome. A responsible mtDNA genetic analysis needs information
that a conventional nuclear GWAS/xQTL resource generally does not provide,
including:

- heteroplasmy thresholds;
- sequencing depth and tissue;
- haplogroup and maternal ancestry;
- mitochondrial copy number;
- NUMT filtering; and
- an mtDNA reference/build and mitochondrial association model.

Because these inputs were absent, Tier 1 could not evaluate 20 candidate-context
units belonging to these six genes. Labeling them negative would be incorrect.

## What the analysis did not establish

Tier 1 does not prove that any Phase 18 key driver is causal. In particular:

- a shared or fine-mapped genetic signal does not by itself prove mediation
  through the candidate gene;
- gene-level AD support does not prove that the effect acts in the Phase 18
  broad cell type;
- the APOE result does not independently validate the astrocyte mechanism;
- the two COX7C context rows are not two replications;
- TWAS membership alone does not establish causality or direction; and
- absence from a filtered summary does not support a claim of no effect.

The correct interpretation is cross-validation: human genetics adds an
independent line of support for a small subset of candidates and identifies
where evidence is currently missing or unassessable.

## Reproducibility and quality controls

The workflow produced a flat, 23-file validated output bundle at:

```text
results/minerva_production/19_genetic_support/
```

The key checks were:

- the Phase 18 checksum matched;
- 47 unique candidate-context units and 25 genes were reconstructed;
- all 25 genes had GENCODE GRCh38 coordinates and HGNC-approved symbols;
- all six external source hashes matched;
- one terminal result was produced for every candidate-context unit;
- four route-assessability records were produced per unit, for 188 total;
- all H0-H4 fields remained missing rather than being inferred from a different
  source score;
- exactly 23 declared output files were published; and
- every declared artifact hash was independently reproduced.

The automated suite also performed a fresh end-to-end build in a temporary
directory and passed all three tests.

## Where to inspect the evidence

The most useful files are:

- `results/minerva_production/19_genetic_support/genetic_support_evidence_summary.tsv`
  — one conclusion row for each of the 47 candidate contexts;
- `results/minerva_production/19_genetic_support/genetic_support_common_variant_evidence.tsv.gz`
  — all regional and direct-target variant evidence;
- `results/minerva_production/19_genetic_support/genetic_support_colocalization.tsv.gz`
  — the eight precomputed candidate-gene records and explicit missing H0-H4;
- `results/minerva_production/19_genetic_support/genetic_support_assessability.tsv`
  — the reason each route is positive, none found, ambiguous, not applicable,
  or not assessable;
- `results/minerva_production/19_genetic_support/genetic_support_checks.tsv`
  — blocking and expected-limitation checks;
- `results/minerva_production/19_genetic_support/genetic_support_status.tsv`
  — the final Tier 1 completion status; and
- `results/minerva_production/19_genetic_support/genetic_support_evidence_matrix.png`
  — a visual summary of all 47 results.

The runnable implementation and frozen configuration are:

```text
scripts/19_run_genetic_support.py
config/phase19_genetic_support.yml
config/phase19_local_production_execution.yml
tests/test_phase19_genetic_support.py
```

## Bottom line and next decision

Tier 1 successfully answered the screening question for all Phase 18
candidates using a small public summary dataset and local computation. It found
strong gene-level support for APOE, limited evidence for COX7C and SELENOW, no
direct mapping in the registered filtered source for the other nuclear genes,
and no suitable data for the mtDNA genes.

The next tier is necessary only if the scientific goal requires one or more of
the following stronger claims:

1. classical signal-level H0-H4 colocalization;
2. exact cell-type functional support;
3. corrected gene-level rare-variant burden comparisons; or
4. mtDNA-specific association analysis.

Running Tier 1 again on Minerva would not resolve these limitations. They
require additional source data, not additional computing power.
