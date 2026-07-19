# Mitochondrial Gene-Tier Composition and Figure 3–6 Eligibility

## Purpose

This document explains:

1. what the project means by a mitochondrial-related gene;
2. how the core, mtDNA-noncoding, and extended tiers were constructed;
3. the composition of the validated 1,300-feature mitochondrial inventory;
4. why the primary Figures 3–6 use only `core_mito`;
5. how many `mito_extended` genes are eligible for each figure comparison; and
6. which extended genes would enter the displayed Part-A tails in an
   `all_mito_related` sensitivity figure.

The counts below describe the validated production handoffs used on
2026-07-19. The primary figures remain `core_mito`; the inclusive
`all_mito_related` results are precomputed sensitivity results and must be
labeled separately if plotted.

## Overview of the three mitochondrial tiers

### 1. Core mitochondrial protein genes

`core_mito_protein` is the primary tier. A feature enters this tier when it
maps to the frozen Human MitoCarta3.0 inventory.

MitoCarta contains proteins with strong evidence of mitochondrial
localization. The tier therefore includes:

- the 13 mtDNA-encoded proteins, such as `MT-ND2`; and
- nuclear-encoded mitochondrial proteins, such as `NDUFS1`, `TFAM`,
  `TOMM20`, and `PINK1`.

The frozen MitoCarta workbook contains 1,136 canonical human genes. The
production handoff contains 1,196 exact `core_mito_protein` feature records
because the workflow preserves exact assay-feature identity, alias/current
symbol mappings, and reference-only records rather than collapsing rows to
one MitoCarta symbol.

This is the primary tier because it represents the most direct and
reproducible definition of a mitochondrial protein gene.

### 2. Mitochondrial-DNA noncoding genes

`mtdna_noncoding` contains the conventional non-protein-coding genes on
GENCODE GRCh38 `chrM`:

- 22 mitochondrial tRNAs; and
- 2 mitochondrial rRNAs.

Together with the 13 mtDNA protein-coding genes already assigned to
`core_mito_protein`, these form the conventional set of 37 mtDNA genes.

The 24 noncoding records are retained explicitly so absence from the
single-nucleus assay is not confused with a tested nonsignificant result. In
the current production handoff, all 24 are reference-only and none can enter
a similarity ranking.

### 3. Extended mitochondrial-associated genes

`mito_extended` contains genes that regulate or respond to mitochondrial
biology but whose products are not necessarily permanent mitochondrial
residents. Examples include upstream biogenesis regulators, autophagy
machinery recruited during mitophagy, and cytosolic or nuclear stress-response
factors.

The extended reference was frozen before examining differential-expression
results. It uses exactly four Reactome V97 pathways:

| Reactome ID | Pathway | Source genes | MitoCarta overlap | Extended-only |
|---|---|---:|---:|---:|
| `R-HSA-1592230` | Mitochondrial biogenesis | 95 | 50 | 45 |
| `R-HSA-5205647` | Mitophagy | 39 | 17 | 22 |
| `R-HSA-9840373` | Cellular response to mitochondrial stress | 9 | 5 | 4 |
| `R-HSA-9841251` | Mitochondrial unfolded protein response (UPRmt) | 18 | 8 | 10 |
| **Union** | **Four-pathway panel** | **157** | **77** | **80** |

The per-pathway counts are not additive because a gene can occur in more than
one pathway. Symbols were normalized through the frozen HGNC 2026-06-05
snapshot before comparison with MitoCarta.

The classification precedence is:

1. MitoCarta member → `core_mito_protein`;
2. mtDNA rRNA or tRNA → `mtdna_noncoding`;
3. remaining member of the four-pathway Reactome panel → `mito_extended`;
4. otherwise → `non_mito`.

Consequently, the 77 Reactome genes already found in MitoCarta remain core.
Only the 80 non-core genes receive the `mito_extended` label. All 80 are
nuclear encoded.

The UPRmt pathway has Reactome review status 3/5, whereas the other three
pathways have status 5/5. The complete extended tier is therefore treated as
secondary or sensitivity evidence.

## How features were annotated

Phase 09 is an annotation and integration step, not another
differential-expression test. Its inputs are:

- exact assay features from the single-nucleus expression objects;
- complete Phase 08 MAST results, including nonsignificant and filtered rows;
- Human MitoCarta3.0;
- GENCODE 44 gene identifiers, chromosomes, and biotypes;
- the frozen HGNC 2026-06-05 current/previous/alias mapping snapshot; and
- the frozen four-pathway Reactome V97 extended reference.

Identifier mapping follows a deterministic precedence:

1. unique stable Ensembl ID;
2. unique current HGNC symbol;
3. unique previous HGNC symbol;
4. unique HGNC alias;
5. otherwise ambiguous or unmapped.

The exact assay feature remains the row identity. HGNC and Ensembl identifiers
annotate that row but do not replace it. This prevents silent collapsing of
distinct assay features that share a symbol or reference mapping.

Phase 09 also distinguishes:

- not present in the expression matrix;
- present but filtered by the expression threshold;
- tested but not significant;
- significantly upregulated; and
- significantly downregulated.

These states are carried into Phase 10 as `-1`, `0`, or `+1` ternary
differential-expression states.

## Validated production inventory

The validated Phase 10 feature manifest is the compact downstream inventory
derived from the Phase 09 annotations.

| Tier | Feature records | Measured | Phase-09 test eligible | Reference only | Scoreable source features | mtDNA encoded | Nuclear encoded |
|---|---:|---:|---:|---:|---:|---:|---:|
| `core_mito_protein` | 1,196 | 1,194 | 1,155 | 2 | 1,194 | 13 | 1,183 |
| `mtdna_noncoding` | 24 | 0 | 0 | 24 | 0 | 24 | 0 |
| `mito_extended` | 80 | 80 | 79 | 0 | 80 | 0 | 80 |
| **Total** | **1,300** | **1,274** | **1,234** | **26** | **1,274** | **37** | **1,263** |

These are feature-record counts, not necessarily unique canonical reference
genes. This distinction explains why the 1,196 core feature records exceed
the 1,136 canonical MitoCarta genes.

### Local-reference versus production eligibility

The extended-reference acquisition manifest recorded 77 of 80 extended genes
as test-eligible in the local Vasculature preflight; `DEFA5`, `PRKAG3`, and
`UBE2V1` were the three local exceptions.

The consolidated production feature manifest spans all nine source RDS sets.
It reports all 80 extended genes as measured and 79 as test-eligible at that
broader feature-manifest scope; only `UBE2V1` has
`zero_or_nonfinite_raw_counts`. These two counts describe different execution
scopes and should not be substituted for the comparison-specific Phase 10
ranking eligibility below.

## From annotation tiers to similarity-ranking universes

Phase 10 defines two prespecified ranking universes:

| Analysis universe | Included tiers | Role |
|---|---|---|
| `core_mito` | `core_mito_protein` | Primary analysis used by Figures 3–6 |
| `all_mito_related` | `core_mito_protein` + `mtdna_noncoding` + `mito_extended` | Inclusive sensitivity analysis |

The Zhang–Yu similarity score is calculated once per feature and comparison.
Universe membership does not alter that score. It changes:

- which features enter the ranking pool;
- the high- and low-score ranks;
- the Benjamini–Hochberg FDR family; and
- the pathway-enrichment background and query composition.

Therefore, extended genes must not simply be appended to an existing
`core_mito` figure. An inclusive figure must use the frozen
`all_mito_related` ranks, FDR values, 200-gene queries, and pathway
backgrounds throughout.

### Coverage requirement for ranking

A numerical score can be calculated from one observed paired state, but such
a score can be spuriously extreme. A feature enters a ranking only when:

```text
required_paired_tests =
  max(3, ceiling(0.50 * structurally_estimable_dimensions))

paired_tests >= required_paired_tests
```

This requirement is applied separately to every comparison. It is why the
number of usable extended genes varies across Figures 3–6 even though the
reference always contains 80 extended genes.

The 24 mtDNA-noncoding genes are reference-only in the current data and
contribute zero ranking-eligible features. Thus, the difference between the
current `core_mito` and `all_mito_related` ranking-pool sizes is entirely due
to eligible extended genes.

## Extended genes available to each figure

### Ranking-eligible extended genes

| Figure or block | Phase 10 comparison | Core eligible | Extended eligible | Inclusive eligible | Extended unavailable from coverage |
|---|---|---:|---:|---:|---:|
| Figure 3 | Female versus Male across APOE groups | 700 | 66 | 766 | 14 |
| Figure 4 | APOE e2 versus e33 across sexes | 708 | 67 | 775 | 13 |
| Figure 5 | APOE e4 versus e33 across sexes | 686 | 65 | 751 | 15 |
| Figure 6, APOE e2 | Female versus Male within e2 | 732 | 66 | 798 | 14 |
| Figure 6, APOE e33 | Female versus Male within e33 | 705 | 65 | 770 | 15 |
| Figure 6, APOE e4 | Female versus Male within e4 | 679 | 64 | 743 | 16 |

“Extended eligible” means that the gene is a member of `mito_extended` and
passes the comparison-specific Phase 10 paired-coverage requirement. It does
not mean the gene will necessarily occur in a displayed top or bottom tail.

### Extended genes that would appear in inclusive Part A

The inclusive Phase 10 rank sets are already frozen. If a separately labeled
`all_mito_related` Part-A sensitivity figure were rendered, the following
extended genes would occur in its displayed tails:

| Figure or block | Requested tail size | Extended in high tail | Extended in low tail | Extended displayed |
|---|---:|---|---|---:|
| Figure 3 | 25 + 25 | `TBL1XR1`, `NCOA2`, `TBK1`, `MED1` | `UBB`, `HSPA1A` | 6 of 50 |
| Figure 4 | 25 + 25 | `TBL1XR1`, `EIF2S3`, `CAMK4` | `UBB`, `NR1D1` | 5 of 50 |
| Figure 5 | 25 + 25 | `UBE2N`, `ATG5`, `CSNK2A1`, `NCOA2`, `TBK1`, `TBL1XR1` | `HSPA1A`, `UBB`, `DNAJA1`, `UBC`, `RPS27A` | 11 of 50 |
| Figure 6, APOE e2 | 10 + 10 | `TBL1XR1` | None | 1 of 20 |
| Figure 6, APOE e33 | 10 + 10 | `HSF1` | `UBB` | 2 of 20 |
| Figure 6, APOE e4 | 10 + 10 | None | `HSPA1A`, `CALM1` | 2 of 20 |

These counts describe the stored inclusive rank sets; they are not obtained by
adding extended genes to the current core-only displayed list.

## Why the manuscript figures use `core_mito`

The primary Figures 3–6 use `core_mito` because:

1. MitoCarta provides direct, curated mitochondrial-protein evidence.
2. The definition was frozen before reviewing the similarity results.
3. Extended genes include indirect regulators and stress machinery that may
   function outside mitochondria.
4. The extended tier is based on a deliberately small four-pathway panel and
   includes one pathway with Reactome review status 3/5.
5. Keeping the extended tier secondary prevents the primary mitochondrial
   definition from expanding to nearly any stress, autophagy, or metabolic
   regulator.

This does not imply that extended genes are unimportant. They answer a
different question:

> Do indirect mitochondrial regulators and stress-response genes alter the
> shared-versus-divergent transcriptional patterns seen in the canonical
> mitochondrial protein set?

That question is best addressed with separately labeled
`all_mito_related` sensitivity figures and tables.

## Relationship to the Figure 3–6 debug tables

The per-figure files under:

```text
docs/dbug/figure_03_to_06/
```

contain all 1,300 feature records for each comparison, including core,
mtDNA-noncoding, extended, reference-only, and coverage-ineligible records.
Figure 6 contains three comparison-specific blocks and therefore has 3,900
rows.

Useful columns include:

- `mito_tier`: core, mtDNA noncoding, or extended;
- `in_core_mito` and `in_all_mito_related`: universe membership;
- `ranking_eligible`: comparison-specific coverage eligibility;
- `primary_core_mito_ranking_member`: eligibility in the primary core pool;
- `high_rank_core_mito` and `low_rank_core_mito`: primary ranks;
- `high_rank_all_mito_related` and `low_rank_all_mito_related`: inclusive
  sensitivity ranks; and
- `displayed_in_part_a`: whether the record appears in the current primary
  heatmap.

Raw similarity scores in those files must not be used to select genes without
first applying the intended universe and `ranking_eligible` requirement.

## Authoritative files

Reference and annotation design:

- `config/phase09_annotation.yml`
- `docs/phase_09_annotate_genes/phase_09_annotate_mitochondrial_genes_plan.md`
- `docs/phase_09_annotate_genes/phase_09_extended_tier_reference_plan.md`
- `data/reference/Human.MitoCarta3.0.xls`
- `data/reference/gencode/gencode.v44.basic.annotation.gtf.gz`
- `data/reference/hgnc/hgnc_complete_set_2026-06-05.txt`
- `data/reference/mitochondrial_extended/mitochondrial_extended_manifest.tsv`

Validated downstream composition and ranking:

- `results/minerva_production/10_similarity/mitochondrial_similarity_feature_manifest.tsv`
- `results/minerva_production/10_similarity/mitochondrial_similarity_results.tsv.gz`
- `results/minerva_production/10_similarity/mitochondrial_similarity_rank_sets.tsv`
- `results/minerva_production/10_similarity/similarity_status.tsv`

The frozen reference hashes and validation statuses in these files are the
provenance authority for the counts reported above.
