# The FunGen-xQTL resource: what it provides and how we use it

**Date:** 2026-08-29
**Applies to:** the Phase 19 Tier 1 screen and the 19b rerun for the
simple-aggregation drivers (`scripts/19b_genetic_support_simple_aggr.py`,
results in `results/minerva_production/19b_genetic_support_tier1/`)
**Presentation references:** "Published results / FunGen fine-mapping" on the
genetic-support deck (source 1 of the three evidence categories)

## 1. What FunGen-xQTL is

FunGen-xQTL is the ADSP Functional Genomics consortium project (NIA/ADSP):
a large, systematic integration of Alzheimer's disease GWAS with brain
molecular QTLs — expression (eQTL), splicing (sQTL), protein (pQTL),
methylation, and chromatin — across many brain cohorts and contexts (ROSMAP,
MSBB, Knight ADRC, MetaBrain, STARNET, and single-cell contexts such as
excitatory/inhibitory neurons, oligodendrocytes, OPCs, astrocytes, and
microglia).

In our three-category evidence scheme it is **category 1: published
results** — ready-made, gene-level integration that we look our drivers up
in, as opposed to categories 2 (disease GWAS) and 3 (brain QTL), which we
must combine ourselves.

## 2. The snapshot we hold

We use the official public GitHub snapshot at commit
`f6f63fc319a417213cf1e86ec0eb14fcb53d2427` (2026-07-29), six files totaling
9,166,810 bytes (~8.74 MiB), checksum-registered by the Tier 1 and Tier 2
input inventories:

| File | Size | Content |
|---|---:|---|
| `unified_AD_loci_xQTL_summary.xlsx` | 8.6 MB | The unified workbook: per-locus and per-gene integration tables (see §3) |
| `AD_loci_unified_cs95orColocs_Pval1e5_variant_level.csv.gz` | 420 KB | Variant-level table: every AD variant in a 95% credible set or with colocalization support at P < 1e-5 |
| `AD_genes_FunGen_AD_GVC_xQTL_20250325.tsv` | 21 KB | Gene list: genes with GVC (gene-variant-consequence) xQTL support |
| `AD_genes_FunGen_AD_twas_GVC_xQTL_20250325.tsv` | 21 KB | Gene list: genes appearing in the consortium TWAS results |
| `context_meta.tsv` | 2 KB | Maps dataset names to cell-type/tissue contexts |
| `statfungen_synapse_staging_folder_structure.yml` | 60 KB | Provenance: the richer Synapse source objects behind the summaries |

Local copies exist under
`data/reference/phase19_genetic_support/source_downloads/` (Tier 1 layout)
and `data/reference/phase19_genetic_support/tier2/source_downloads/` (Tier 2
layout); the copies are byte-identical across both machines. The two small
gene lists are additionally frozen with the rerun plan under
`docs/phase_19_genetic_support/simple_aggr_rerun/frozen_inputs/`.

## 3. What the resource provides

### 3.1 AD fine-mapping (variant level)

Fine-mapping is the statistical step after GWAS. A significant GWAS region
contains dozens to hundreds of correlated variants (linkage disequilibrium),
so the lead P value alone cannot say *which* variant is causal. Fine-mapping
(SuSiE-style methods) converts the regional evidence into:

- an **inclusion score** per variant (posterior probability that this
  specific variant is causal for the AD association; 1.0 ≈ certain, 0.2 ≈
  one plausible candidate among several); and
- **95% credible sets** — the smallest set of variants that contains the
  causal variant with 95% probability.

The variant-level CSV carries, per variant: position, rsID, the maximum
inclusion score and the method that produced it, credible-set membership
(`is.cs95`), minimum AD P value across the contributing GWAS, the GWAS
sources, and a cV2F functional prioritization score.

### 3.2 Variant→gene assignment (the "Gene Locus table")

The unified workbook's Gene Locus table (4,796 rows; 4,684 with a target
gene; 544 unique target genes) is the core product for us: each row links a
fine-mapped AD variant to an **xQTL target gene**, i.e., the gene whose
molecular regulation the consortium's evidence connects to that variant. Per
row it records:

- the variant (rsID, position), its AD inclusion score and minimum AD P;
- the target gene and gene ID;
- the xQTL evidence behind the assignment, per modality and dataset:
  fine-mapping PIPs, **colocalization VCP** (variant colocalization
  probability), multi-context fine-mapping PIPs, TWAS z-scores, and MR and
  cTWAS significance flags;
- context detail (which cell types/tissues, with **CL1–CL6 confidence
  labels** and dataset counts); and
- extras: trans-xQTL effects, multi-gene mvSuSiE credible sets, sex and
  APOE-interaction QTL P values where tested.

Cell-type sheets (Brain, Exc, Inh, Oli, OPC, Ast, Mic, Immune) repeat the
integration restricted to one context.

### 3.3 Gene lists (TWAS and GVC)

Two flat lists name genes with consortium TWAS support or
gene-variant-consequence xQTL support. They contain gene identity and source
resources only — no effect sizes, P values, or replication detail — so
membership alone is weak evidence (this is how SELENOW keeps its "weak"
grade).

### 3.4 Colocalization — what FunGen does and does not provide

FunGen **does** run same-variant-style integration: the variant table records
detection methods such as `ADxAD_coloc` and `ADxQTL_coloc`, and the gene
table carries per-dataset colocalization VCP values. When FunGen assigns a
variant to a gene, that assignment typically rests on exactly the GWAS + QTL
combination logic of our design — done by the consortium, at scale.

It does **not**, however, satisfy our prespecified same-variant contract:

1. **Different statistic, not auditable.** The public files publish summary
   quantities — inclusion scores, VCP, CL confidence classes — not classical
   H0–H4 colocalization posteriors (PP.H4) under prespecified priors. The
   frozen Phase 19 rule explicitly forbids reinterpreting PIP, VCP, or CL
   labels as PP.H4.
2. **Not reproducible from the snapshot.** The complete fitted QTL models,
   exact variant orders, and source-matched LD behind their colocalizations
   are not public — the same gap that blocks our own APOE and RPS15 tests.
3. **Does not settle gene ownership in dense loci.** One fine-mapped variant
   can be assigned to many target genes; at the chr16p11.2 locus the lead
   variant rs1140239 is assigned to 25 genes (including our drivers PPP4C
   and SEPHS2, which share all 30 of their mapped variants).
4. **Phenotype scope.** The integration targets clinical AD; our CSF
   biomarker routes (e.g., the MAP1LC3B tau signals) have no FunGen
   colocalization at all.

## 4. How the 19b screen uses it

For each of the 433 frozen drivers, the screen reads three things: direct
Gene Locus table mappings (by symbol, then Ensembl ID), TWAS/GVC list
membership, and window-level variant annotation (fine-mapped variants inside
the gene ± 1 Mb window, reported separately and never graded). The frozen
grade rules:

| Grade | Rule |
|---|---|
| `strong` | direct mapping with min AD P < 5e-8 **and** inclusion score ≥ 0.5 |
| `moderate` | direct mapping with min AD P < 5e-8 and inclusion ≥ 0.1, or a workbook TWAS/cTWAS-significant flag |
| `weak` | any other direct mapping, or TWAS/GVC list membership only |
| `none_found` | absent from all published summaries |

Results on the 433 drivers: 8 strong (APOE, PLCG2, STAG3, PPP4C, SEPHS2,
ZNF251, ZNF652, AC087500.1), 3 moderate (INTS8, DGKQ, TPCN1), 17 weak,
405 none found.

### Worked examples

- **APOE** — the cleanest case: rs429358 (the ε4 coding variant) mapped
  directly, inclusion score 1.0, AD P ≈ 1.9e-155.
- **PLCG2** — rs4407053 assigned with inclusion 0.76 at P = 8.2e-12 (plus
  two further variants and GVC membership). Note: the famous protective
  missense rs72824905 sits in PLCG2's window with inclusion 0.996 but is
  assigned by FunGen to **BCO1**, so we do not claim it for PLCG2.
- **ZNF251** — only two mapped variants, but both with inclusion ≈ 1.0.
- **PPP4C / SEPHS2** — the ambiguity case: strong scores inherited from a
  25-gene shared assignment at one chr16 locus; locus-confident,
  gene-ambiguous.
- **COX7C** (from the original screen) — a single bulk sQTL record with
  confidence label CL5 projected onto two candidate contexts: one source
  observation, not two replications.
- **RPS15** — deliberately `none_found` here despite its strong AD region:
  FunGen never published a direct mapping for it, so its case rests on the
  regional GWAS and brain-QTL evidence instead.

## 5. Correct interpretation

- A FunGen "direct mapping" is **published evidence that a causal AD variant
  regulates this gene** — strong screening evidence, but produced by the
  consortium's pipeline choices, not by our auditable analysis.
- Assignments are **not exclusive**: in gene-dense, high-LD loci several
  neighboring genes can legitimately carry the same variants. Grade strength
  should be read together with how many genes share the assignment.
- Absence (`none_found`) means absence from these published summaries, not
  absence of genetic involvement (RPS15 is the standing example).
- FunGen evidence therefore feeds — but never replaces — the final step of
  our design: the prespecified H0–H4 same-variant test with complete models
  and matched LD, which remains blocked by public data gaps for every driver.

## 6. Related files

- Tier 1 (original 25-gene screen): `results/minerva_production/19_genetic_support_tier1/`
- 19b full-list screen: `results/minerva_production/19b_genetic_support_tier1/fungen_gene_evidence.tsv`
- Rerun plan: [`simple_aggr_rerun/phase19_simple_aggr_rerun_plan.md`](simple_aggr_rerun/phase19_simple_aggr_rerun_plan.md)
- Consolidated Phase 19 results: [`phase19_genetic_support_results_summary.md`](phase19_genetic_support_results_summary.md)
