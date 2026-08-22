# Phase 19 human genetic support: consolidated results summary

**Status:** four registered public-data workstreams completed; broader genetic validation remains incomplete<br>
**Current through:** 2026-08-21<br>
**Scope:** 25 unique Phase 18 genes in 47 gene-by-network candidate contexts

## Executive summary

Phase 19 asked whether inherited human genetic variation supports the Phase 18
ROSMAP key-driver genes and, when the required data existed, whether an
Alzheimer disease (AD) or AD-endophenotype association shared an association
signal with a molecular QTL for the same gene.

This document is a synthesis of the frozen Phase 19 outputs, not a new
association analysis. No alternative thresholds, subgroups, or tests were
searched after viewing the results.

The main conclusions are:

- **APOE is the only Phase 18 gene with strong genetic support.** Tier 1
  directly mapped the fine-mapped AD coding variant `rs429358` to `APOE`
  (inclusion score `1.0`, minimum reported AD P approximately `1.88e-155`).
  APOE also passed both the regional-GWAS and candidate-corrected MAGMA gates
  for CSF amyloid-beta 42, total tau, and p-tau181.
- **COX7C and SELENOW have weak or suggestive summary evidence.** COX7C has
  one weak bulk-brain sQTL record projected to two Phase 18 contexts; these are
  not independent replications. SELENOW appears in a TWAS gene list for which
  no model statistic or exact cell context was released.
- **RPS15 is promising but unresolved.** Its AD region is strongly associated
  (`P = 4.089e-30`), and several bulk-brain QTL tracks are signal-positive.
  However, none supplied the complete multi-signal QTL model and source-matched
  LD required by the primary contract to test whether the AD association shares
  a signal with an RPS15 QTL. Exact OPC and inhibitory-neuron support was not
  established.
- **ANKRD11 has a significant regional AD signal, but not gene-level support.**
  Its tested eQTL did not pass the QTL signal gate and its sQTL route was not
  assessable. Proximity of a gene to a GWAS signal is not causal assignment.
- **No completed extension validated a new gene.** Tier 2 produced zero valid
  primary H0-H4 shared-signal analyses; the CSF endophenotype extension added zero
  newly supported genes; and the OPC/RPS15 recovery added zero validated genes.
- **Fifteen of the 19 nuclear genes lacked a genome-wide-significant regional
  signal in the tested clinical-AD GWAS.** None of the 18 non-APOE nuclear
  genes passed either CSF endophenotype follow-up gate.
- **The six mtDNA genes were not tested negatively.** They were explicitly
  `not_assessable` because nuclear GWAS/cis-QTL/LD methods do not test mtDNA
  variation, heteroplasmy, haplogroup, copy number, or NUMT-aware effects.

The correct overall interpretation is therefore not “Phase 19 disproved the
other key drivers.” It is that one gene is strongly supported, two have weak
summary support, one has promising but unresolved QTL evidence, and the rest
are divided between signal-negative tests and routes that the available data
could not validly evaluate.

## 1. Setup and analysis design

### 1.1 Phase 18 candidate freeze

The candidate set was fixed before the Phase 19 genetic results were examined.
The authoritative source was
[`call_key_driver_returns.tsv`](../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv),
frozen at SHA-256
`b917f70e6edcdf030f63e88ba8fbc5b22b80714599c12c80ea449e8c38bd51d8`.
Rows with `top5_display = TRUE` were deduplicated by
`key_driver + broad_network + case_id`; genes were not reranked using genetic
evidence. The archived `key_driver_top5.tsv` was not used because it belongs to
the deprecated three-case selection scheme; the current classes are
`mt_driver` and `non_mt_driver`.

This produced:

| Unit | Count |
|---|---:|
| Phase 18 candidate contexts | 47 |
| Unique genes | 25 |
| Nuclear genes | 19 |
| mtDNA genes | 6 |
| Nuclear candidate contexts | 27 |
| mtDNA candidate contexts | 20 |
| Broad networks | 7 |

The 47 contexts are the displayed/top-five subset of 78 Phase 18 candidate
units that passed the network-analysis gates. Phase 18 selected genes using
network topology, conservative run-level support, cross-run ACAT aggregation,
multiple-testing correction, and within-network ranking. It therefore supports
a **network-associated driver** interpretation, not inherited causal-gene
status by itself. The selection contract is documented in the
[Phase 18 key-driver selection process](../phase_18_key_driver_selection/key_driver_selection_process.md).

The exact displayed lists were:

| Broad network | MT-driver list, in Phase 18 rank order | Non-MT-driver list, in Phase 18 rank order |
|---|---|---|
| Astrocytes | MT-CO2, MT-CO3, MT-ATP6, COX7C, COX4I1 | RPL11, RPLP1, RPL15, APOE, LAPTM4A |
| Excitatory neurons | MT-CO2, UQCR10, COX4I1, COX6B1, MT-CYB | RPL11, RPS13, SELENOW, LAMTOR5, DYNLT1 |
| Inhibitory neurons | MT-CO2, MT-CO3, MT-CYB, MT-ND5, COX7C | RPS15, LAMTOR5, RPLP1, ATP6V1F, RPL38 |
| Microglia | MT-CO2, MT-ND4 | RPL11 |
| OPCs | MT-CO3, MT-CO2, MT-ND4 | RPS15, FTL, ANKRD11, NCOA1 |
| Oligodendrocytes | MT-CO2, MT-ND4 | RPL11 |
| Vasculature cells | MT-CO3, MT-CO2, MT-ATP6, MT-ND4 | None |

“MT driver” is a Phase 18 signature class, not a statement about genome of
origin. For example, `COX7C` and `UQCR10` are nuclear genes in the MT-driver
class. The six actual mtDNA genes are `MT-ATP6`, `MT-CO2`, `MT-CO3`, `MT-CYB`,
`MT-ND4`, and `MT-ND5`.

Gene symbols were validated against the HGNC complete set dated 2026-06-05,
and gene intervals/Ensembl identifiers came from GENCODE v44 basic on GRCh38.
All 25 genes mapped uniquely. Nuclear discovery windows were the gene body plus
1 Mb on each side, but a regional association was never treated as proof that
the candidate gene caused the association.

### 1.2 Staged evidence design

The analysis used a gated design:

```text
frozen Phase 18 gene and cell context
    -> regional AD or endophenotype GWAS signal
        -> candidate-gene molecular-QTL coverage and signal
            -> allele/build/model compatibility and source-matched LD
                -> multi-signal fine-mapping and primary H0-H4 shared-signal analysis
```

A route stopped as soon as an upstream requirement failed. The resulting
states have different meanings:

| State | Meaning |
|---|---|
| `none_found` | No direct support was found in the registered screen; not proof that evidence does not exist. |
| `no_regional_gwas_signal` | The complete tested candidate region had no variant below the frozen GWAS threshold. |
| `no_regional_qtl_signal` | The gene was measured in complete regional QTL data but failed the prespecified QTL signal threshold. |
| `not_assessable` | Required measurement, complete statistics, model, or release metadata were unavailable. |
| `model_or_ld_incompatible` | GWAS and QTL signals existed, but valid shared-signal modeling could not be performed. |
| `not_applicable_mtdna` | The nuclear GWAS/QTL framework was not applicable to the mitochondrial genome. |

The main frozen rules were:

- regional GWAS signal: `P < 5e-8`;
- dense QTL signal in recovery: `P < 0.05 / tested regional variants` for the
  gene and dataset;
- CSF MAGMA threshold: `0.05 / (19 genes × 3 biomarkers) = 8.77193e-4`;
- primary colocalization priors: `p1 = 1e-4`, `p2 = 1e-4`, `p12 = 5e-6`;
- strong shared-signal rule: `PP.H4 >= 0.80` and conditional H4
  `PP.H4 / (PP.H3 + PP.H4) >= 0.80`;
- exact cell context was preferred, followed by a prespecified lineage or
  bulk-brain fallback;
- PIP, credible-set overlap, source “inclusion scores,” VCP, and CL1-CL6 labels
  were not renamed or interpreted as `PP.H4`.

### 1.3 Workstreams

The four conceptual workstreams produced five result bundles because Tier 2
was published first as a regional coverage audit and then as a targeted
multi-signal-colocalization recovery increment.

| Workstream | Primary question | Published result directory |
|---|---|---|
| Tier 1 | Does a compact public AD fine-mapping/xQTL/TWAS/GVC summary directly map evidence to any frozen gene? | [`19_genetic_support_tier1`](../../results/minerva_production/19_genetic_support_tier1/) |
| Tier 2 regional | Do full regional AD GWAS data and released QTL fine-mapping summaries provide valid inputs for the primary multi-signal H0-H4 analysis? | [`19_genetic_support_tier2_regional`](../../results/minerva_production/19_genetic_support_tier2_regional/) |
| Tier 2 recovery | Can targeted dense eQTL/sQTL data and released models resolve the Tier 2 routes? | [`19_genetic_support_tier2_recovery`](../../results/minerva_production/19_genetic_support_tier2_recovery/) |
| CSF endophenotype extension | Do amyloid-beta 42, total-tau, or p-tau181 GWAS reveal candidate signals missed by clinical diagnosis? | [`19_genetic_support_endophenotype_gwas_qtl_extension`](../../results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension/) |
| OPC/RPS15 public recovery | Can already-local, small public QTL resources resolve RPS15 in OPCs or inhibitory neurons? | [`19_genetic_support_opc_rps15_public_recovery`](../../results/minerva_production/19_genetic_support_opc_rps15_public_recovery/) |

All workstreams ran locally by direct execution. `minerva_production` is the
repository publication namespace; it does not mean Minerva compute was used.

## 2. Datasets acquired and why they were used

The tables below summarize the source acquisitions recorded by the published
input inventories and execution reports. Large raw-source directories are
ignored from version control and are not all present in this checkout, so
“acquired” means recorded and checksum-validated by the original execution
bundle unless otherwise noted in the provenance caveats.

### 2.1 Candidate and annotation inputs

| Dataset | Version/content | Use |
|---|---|---|
| Phase 18 KDA results | Current `call_key_driver_returns.tsv`; 95,557 explicit gene-by-run rows | Reconstruct and freeze the 47 candidate contexts without using genetic results. |
| GENCODE | v44 basic, GRCh38 | Map nuclear genes to stable Ensembl IDs and genomic intervals. |
| HGNC complete set | 2026-06-05 | Validate approved gene symbols and distinguish nuclear from mtDNA genes. |

### 2.2 Tier 1 public summary screen

Tier 1 downloaded six files from the official FunGen-xQTL public GitHub
snapshot at commit `f6f63fc319a417213cf1e86ec0eb14fcb53d2427`
(2026-07-29). Together they occupied 9,166,810 bytes, approximately 8.74 MiB.

| File/content | Use |
|---|---|
| `unified_AD_loci_xQTL_summary.xlsx` | Screen precomputed AD GWAS, fine-mapping, and xQTL evidence. |
| `AD_loci_unified_cs95orColocs_Pval1e5_variant_level.csv.gz` | Recover variants, credible-set membership, source inclusion scores, AD P values, and direct candidate mappings. |
| `AD_genes_FunGen_AD_GVC_xQTL_20250325.tsv` | Gene-membership cross-check only; it does not contain a complete rare-variant burden result. |
| `AD_genes_FunGen_AD_twas_GVC_xQTL_20250325.tsv` | Screen whether a candidate appears in the public TWAS/GVC lists. |
| `context_meta.tsv` | Classify exact, lineage, bulk-brain fallback, and mismatched QTL contexts. |
| `statfungen_synapse_staging_folder_structure.yml` | Record provenance and the richer source objects needed for later modeling. |

No individual-level genotypes or phenotypes were downloaded. The richer
Synapse regional statistics, models, and LD objects were registered but were
not readable by the configured account.

### 2.3 Tier 2 regional AD GWAS and QTL coverage

| Dataset | Recorded acquisition | Use |
|---|---:|---|
| Bellenguez 2022 AD GWAS, GWAS Catalog `GCST90027158` | Full GRCh38 summary statistics, 755,201,909 bytes; European-dominant meta-analysis. The recovery manifest and regional summary disagree on the encoded case/control counts; see the reproducibility caveats. | Test every nuclear candidate region for a clinical-AD association and supply dense GWAS statistics. |
| NIAGADS `NG00184.v1` bulk eQTL fine mapping | 365,291,520 bytes | Candidate eQTL/PIP/credible-set coverage. |
| NIAGADS `NG00184.v1` sQTL fine mapping | 563,374,080 bytes | Candidate splice-QTL/PIP/credible-set coverage. |
| NIAGADS `NG00184.v1` single-nucleus eQTL fine mapping | 313,733,120 bytes | Cell-context QTL coverage. |
| NG00184 metadata/manifests | JSON/text, child manifests, combined manifest | Source identity, checksum, context, and model metadata. |
| NG00184 gene endpoint | One significant-only table per nuclear gene | Coverage screen only; never used as dense custom-colocalization input. |

The sources were streamed rather than recursively unpacked. This yielded:

- 311,180 unfiltered regional GWAS rows across all 19 nuclear genes, with
  13,612-23,085 variants per locus;
- 9,363 candidate QTL fine-mapping rows: 2,696 bulk eQTL, 1,473 single-nucleus
  eQTL, and 5,194 sQTL rows; and
- 1,418 QTL rows assigned to a released 95% credible set.

These data established regional signal and released fine-mapping coverage, but
they did not contain the complete compatible QTL model/LD combination required
by the preregistered primary multi-signal colocalization contract.

### 2.4 Tier 2 targeted recovery

The recovery workstream used six preregistered eQTL Catalogue r7 datasets:

| Dataset IDs | Study/context | Assay | Sample size | Reason for use |
|---|---|---|---:|---|
| `QTD000559`, `QTD000563` | Young 2019 naive microglia | eQTL, LeafCutter sQTL | 104 | Exact microglial match. |
| `QTD000569`, `QTD000573` | Aygun 2021 neurons | eQTL, LeafCutter sQTL | 73 | Neuronal-lineage match. |
| `QTD000579`, `QTD000583` | Walker 2019 neocortex | eQTL, LeafCutter sQTL | 211 | Prespecified bulk-neocortex fallback for astrocytes, OPCs, and other contexts. |

Nineteen public source files totaling 2,959,598,125 bytes were acquired and
checksum-registered: pinned eQTL Catalogue metadata, six SuSiE log-Bayes-factor
archives, six credible-set archives, three LeafCutter conditional/event files,
and the NIAGADS `NG00067.v21` public registry used to inventory possible ADSP
LD. Because the released SuSiE archives omitted the target traits, direct
FTP/tabix range access extracted 62,551 candidate-region eQTL rows without
downloading the entire dense archives.

### 2.5 CSF endophenotype GWAS and APOE molecular-QTL follow-up

The primary endophenotype datasets were complete official GWAS Catalog files:

| Trait | Accession | Ancestry/sample size | Valid autosomal rows | Use |
|---|---|---:|---:|---|
| CSF amyloid-beta 42 | `GCST90726396` | European, 18,948 | 7,345,582 | Test a quantitative amyloid phenotype closer to AD pathology. |
| CSF total tau | `GCST90726397` | European, 18,948 | 7,346,530 | Test total-tau biology. |
| CSF p-tau181 | `GCST90726398` | European, 18,948 | 7,396,296 | Test phosphorylated-tau biology. |

For each trait, the raw complete file, harmonized GRCh38 file, tabix index, and
metadata were recorded. All 19 nuclear regions passed coverage. MAGMA v1.10
used the official FUMA 1000 Genomes Phase 3 European LD reference with dbSNP151
synonyms and the Ensembl v110 **GRCh37** gene-location file. This reference was
used for MAGMA gene-based tests only, not as substitute QTL-cohort LD for
colocalization.

Only APOE passed the frozen GWAS/MAGMA gates, so the QTL follow-up was restricted
to APOE. The execution report states that the following molecular inputs were
obtained and checksum-verified; however, the published input inventory does not
independently substantiate the four NG00130.v2 files listed first (see the
reproducibility caveats):

- four complete `NG00130.v2` CSF APOE pQTL files: total APOE
  (`GCST90424891`), E3 (`GCST90425531`), E4 (`GCST90425532`), and E2
  (`GCST90426314`);
- eight `NG00184.v1` HMT-significant/fine-mapping archives across eQTL, pQTL,
  sQTL, and single-nucleus eQTL, totaling 4,197,416,960 bytes, plus metadata;
- targeted eQTL Catalogue bulk-neocortex eQTL/sQTL data; and
- Timsina 2026 supplementary tables for publication-level cross-checks, not
  as the primary evidence source.

scMetaBrain 2026 and PsychAD single-nucleus eQTL were registered for potential
exact-cell follow-up but remained unassessable from the locally obtainable
public inputs.

### 2.6 OPC/RPS15 public-data recovery

This workstream downloaded **zero new source bytes**. It reused the eight
already-local NG00184 archives, their metadata, and 280 extracted chromosome-19
members totaling 210,334,198 bytes. It measured RPS15 across eligible OPC,
inhibitory-neuron, brain eQTL, sQTL, pQTL, and single-nucleus routes without
forcing a full-archive download.

### 2.7 Important data that were not acquired or used

- The complete NG00184 association archives were not downloaded. The four
  registered archives total approximately 844 GB using the later component
  estimates (about 821 GB under the earlier three-modality estimate) and did
  not satisfy the local small-data/storage contract.
- ADSP R5 non-Hispanic White LD and 1000 Genomes 30x European LD for primary
  colocalization were registered but not processed after the upstream QTL-model
  gates failed. GWAS LD was not substituted for QTL-study LD.
- No controlled individual-level WGS, custom rare-variant burden data, formal
  sex/APOE interaction data, or mtDNA association dataset was acquired.
- Significant-only gene tables were not used to declare a measured negative
  result when the set of all tested genes/events was unknown.

## 3. Genetic support found

### 3.1 Formal cumulative grades

The frozen 47-context Tier 1 matrix reported:

| Formal grade | Candidate-context rows | Unique-gene interpretation |
|---|---:|---|
| Strong | 1 | APOE |
| Moderate | 0 | None |
| Weak | 3 | COX7C in two contexts from one source record; SELENOW in one context |
| None found | 23 | No direct mapping in the registered summary; not proof of absence |
| Not assessable | 20 | Six mtDNA genes represented in 20 contexts |

The [Tier 1 evidence matrix](../../results/minerva_production/19_genetic_support_tier1/genetic_support_evidence_matrix.png)
visualizes these context-level grades. The specialized RPS15 workstream later
assigned RPS15 a separate weak/suggestive result, but this was not reintegrated
into the formal 47-row cumulative grade, where RPS15 remains `none_found`.

### 3.2 APOE: strong support, unresolved exact astrocyte mechanism

APOE has the strongest and most direct genetic evidence:

- `rs429358` (`chr19:44908684:T:C`) was directly mapped to APOE, was in a 95%
  credible set, had AD inclusion score `1.0`, and had minimum reported AD
  `P = 1.8796e-155`;
- two additional direct APOE records were `rs73045691` (inclusion score
  `0.5493`, `P = 1.19e-21`) and `rs34041051` (inclusion score `0.1061`,
  `P = 7.89e-21`); and
- the Bellenguez candidate window was extremely significant, with the stored
  regional minimum P underflowing numerically to zero.

The Walker bulk-neocortex fallback also contained a significant APOE eQTL
(`P = 9.51257e-8`, threshold `4.33952e-6`). That result could not be converted
into a primary shared-signal claim because the released QTL SuSiE model did not
include APOE and source/ancestry-matched QTL LD was unavailable. It supports a
brain regulatory hypothesis but does not validate an astrocyte-specific
mechanism.

APOE was also the only candidate passing either CSF endophenotype gate:

| CSF trait | Regional minimum P | MAGMA gene-body P | MAGMA +/-10 kb P |
|---|---:|---:|---:|
| Amyloid-beta 42 | Numerical underflow to `0` | `5e-10` | `2.3037e-14` |
| Total tau | `5.4e-161` | `5e-10` | `1.2218e-13` |
| p-tau181 | `3.27e-174` | `5e-10` | `5e-10` |

The APOE QTL audit found a source-significant bulk-brain sQTL and suggestive
CSF APOE protein evidence. At the primary prior, a single-signal sensitivity
analysis of total APOE CSF pQTL produced `PP.H4` approximately `0.999638` for
all three biomarkers. In contrast, the bulk-neocortex APOE eQTL sensitivity
favored distinct signals (`PP.H3` approximately `0.99053`; `PP.H4`
approximately `0.000345`). Both analyses are explicitly
`not_graded_sensitivity_only`: APOE is a multi-signal locus, and the primary
multi-signal QTL model/LD contract was not met.

Thus, APOE is strongly supported as an AD gene, but Phase 19 did **not** prove
that the AD or CSF biomarker association acts through APOE expression or
splicing in the exact Phase 18 astrocyte context. The endophenotype workstream
therefore contributed weak biomarker-specific statistical evidence; APOE's
cumulative strong grade came from Tier 1 and was neither upgraded nor
downgraded by the extension.

### 3.3 COX7C: weak direct mapping plus a regional AD locus

COX7C received a weak Tier 1 grade from one bulk ROSMAP anterior-caudate sQTL
record, `rs2010322`:

- AD `P = 2.6423e-6`, not genome-wide significant;
- xQTL inclusion score `0.02637`;
- source confidence label `CL5`; and
- context was bulk brain, not an exact astrocyte or inhibitory-neuron result.

The same record was projected to the astrocyte and inhibitory-neuron candidate
rows. This is one source observation, not two independent confirmations.

The larger Bellenguez scan found a genome-wide-significant signal in the COX7C
candidate window (`P = 8.579e-14`, lead `rs62375397`). However, COX7C did not
pass the dense eQTL gate in Aygun neurons (`P = 9.24749e-4`, threshold
`7.08115e-6`) or Walker neocortex (`P = 2.58275e-3`, threshold `5.16689e-6`).
The full sQTL routes remained unassessable, and none of the CSF traits passed a
COX7C regional or MAGMA gate. The final evidence therefore remains weak rather
than a validated causal-gene assignment.

### 3.4 SELENOW: suggestive TWAS-list membership only

SELENOW appears in the public FunGen-xQTL TWAS gene list, but the released list
does not include a model-level effect, P value, replication result, or exact
excitatory-neuron context. Its Bellenguez regional minimum P was `6.41e-5`, and
it passed neither regional nor MAGMA gates for any CSF biomarker. This is weak
screening evidence only.

### 3.5 RPS15: suggestive public QTL evidence, no gene or context validation

The RPS15 candidate window contained a strong AD association
(`P = 4.089e-30`, lead `rs12151021`). In the Tier 2 recovery:

- Walker bulk-neocortex RPS15 eQTL passed the gene-specific gate
  (`P = 2.11971e-6`, threshold `3.75883e-6`);
- Aygun neuronal RPS15 eQTL did not pass (`P = 1.93132e-4`, threshold
  `5.03474e-6`); and
- no compatible candidate-specific QTL SuSiE model or source-matched LD was
  available for the positive bulk route.

The later public-data audit had 37 eligible source/context routes, measured 31,
and found six positive candidate-context rows. Those six rows represent the
same three fallback bulk-brain tracks repeated across the OPC and inhibitory
Phase 18 contexts:

| Underlying source track | QTL result | Main limitation |
|---|---|---|
| MSBB BA36 eQTL | Minimum P `2.41403e-7`, FDR `0.00209909` | Bulk brain; no complete fitted model/source LD. |
| ROSMAP DLPFC sQTL | Minimum P `3.86842e-30`, FDR `1.26188e-26`, maximum PIP `1.0` | Bulk brain, ROSMAP-overlapping, incomplete primary modeling inputs. |
| ROSMAP posterior-cingulate sQTL | Minimum P `3.30886e-7`, FDR `0.000858045`, maximum PIP `0.910283` | Same limitations. |

The exact OPC and inhibitory-neuron single-nucleus routes did not contain a
source-significant RPS15 QTL. All positive routes had `PP.H4 = NA`; zero H0-H4
analyses were resolved, so `PP.H4` was unavailable rather than equal to zero.
The specialized result is therefore
`weak`/`suggestive_public_support_only`, with `gene_validated = FALSE` and
`context_validated = FALSE`.

### 3.6 ANKRD11: significant region, no candidate-gene assignment

The ANKRD11 candidate window was genome-wide significant in the clinical-AD
GWAS (`P = 1.283e-11`, lead `rs56407236`). The Walker bulk-neocortex eQTL did
not pass its gene-specific signal threshold (`P = 1.81941e-4`, threshold
`4.52161e-6`), and the sQTL event was absent from the detected-event/model
release, leaving measurement status unresolved. ANKRD11 also failed the CSF
regional and MAGMA gates. Its cumulative grade remains `none_found`.

### 3.7 Route-level and endophenotype accounting

The Tier 2 recovery converted the original generic 54-route “not assessable”
result into more informative terminal states:

| Terminal state | Routes | Interpretation |
|---|---:|---|
| `no_regional_gwas_signal` | 42 | Complete clinical-AD regions failed `P < 5e-8`. |
| `no_regional_qtl_signal` | 4 | Complete dense eQTL regions were present but failed the gene-specific QTL gate. |
| `model_or_ld_incompatible` | 2 | Both regional GWAS and eQTL signals existed for APOE or OPC RPS15, but primary modeling inputs were incompatible/incomplete. |
| `not_assessable` | 6 | Target sQTL event absent from a detected-event/model release; measurement status unresolved. |
| Valid H0-H4 results | 0 | No route passed every primary input gate. |

The endophenotype extension screened all 19 nuclear genes against three traits,
creating 57 terminal gene-biomarker decisions:

- three `regional_and_gene_based_signal` decisions, all APOE;
- 54 `no_qualifying_gwas_signal` decisions, covering every other nuclear
  gene across all three traits;
- 27 APOE QTL routes, split into nine `model_or_ld_incompatible`, nine
  `no_regional_qtl_signal`, and nine `not_assessable`; and
- zero newly biomarker-supported genes.

### 3.8 Candidate-level audit table

| Gene(s) | Phase 18 context(s) | Phase 19 result | Current interpretation |
|---|---|---|---|
| APOE | Astrocytes | Strong direct AD fine mapping; diagnosis and all three CSF regions significant; QTL mechanism unresolved | Strong gene-level support; exact astrocyte mechanism not validated |
| COX7C | Astrocytes, inhibitory neurons | One weak bulk sQTL record; significant diagnosis-GWAS region; tested eQTLs failed the frozen signal gates; sQTL incomplete | Weak/suggestive, not replicated across contexts |
| SELENOW | Excitatory neurons | TWAS-list membership; no diagnosis or CSF regional signal | Weak/suggestive only |
| RPS15 | Inhibitory neurons, OPCs | Significant diagnosis region; bulk-neocortex eQTL and three fallback public tracks; zero resolved H0-H4 analyses (`PP.H4` unavailable) | Separate weak/suggestive result; gene and exact contexts unvalidated |
| ANKRD11 | OPCs | Significant diagnosis region; tested eQTL failed the frozen signal gate; sQTL unassessable | Regional proximity only |
| ATP6V1F | Inhibitory neurons | No qualifying diagnosis or CSF signal | No support found in the tested common-variant design |
| COX4I1 | Astrocytes, excitatory neurons | No qualifying diagnosis or CSF signal | Same |
| COX6B1 | Excitatory neurons | No qualifying diagnosis or CSF signal | Same |
| DYNLT1 | Excitatory neurons | No qualifying diagnosis or CSF signal | Same |
| FTL | OPCs | No qualifying diagnosis or CSF signal | Same |
| LAMTOR5 | Excitatory, inhibitory neurons | No qualifying diagnosis or CSF signal; two Tier 2 sQTL routes lacked released coverage | No support found; some route coverage incomplete |
| LAPTM4A | Astrocytes | No qualifying diagnosis or CSF signal | No support found in the tested common-variant design |
| NCOA1 | OPCs | No qualifying diagnosis or CSF signal | Same |
| RPL11 | Astrocytes, excitatory neurons, microglia, oligodendrocytes | No qualifying diagnosis or CSF signal | Same |
| RPL15 | Astrocytes | No qualifying diagnosis or CSF signal | Same |
| RPL38 | Inhibitory neurons | No qualifying diagnosis or CSF signal | Same |
| RPLP1 | Astrocytes, inhibitory neurons | No qualifying diagnosis or CSF signal | Same |
| RPS13 | Excitatory neurons | No qualifying diagnosis or CSF signal | Same |
| UQCR10 | Excitatory neurons | No qualifying diagnosis or CSF signal | Same |
| MT-ATP6, MT-CO2, MT-CO3, MT-CYB, MT-ND4, MT-ND5 | 20 contexts across all seven networks | Nuclear GWAS/QTL routes not applicable | Not assessed; no negative mtDNA conclusion is permitted |

## 4. Why Phase 18 key drivers may lack Phase 19 genetic support

Several explanations can coexist. The first group is directly demonstrated by
the Phase 19 files; the second group consists of plausible biological
interpretations that the current analysis cannot distinguish.

### 4.1 File-evidenced reasons

1. **Phase 18 and Phase 19 ask different causal questions.** Phase 18 identifies
   genes whose network neighborhoods are enriched for disease-associated
   mitochondrial signatures. It does not claim that germline variants in those
   genes initiate disease.
2. **Most nuclear genes failed the upstream clinical-AD signal gate.** Fifteen
   of 19 nuclear candidate regions had no variant at `P < 5e-8`. Under the
   registered conservative design, these routes stopped at that gate; changing
   software would not change their prespecified terminal state.
3. **A nearby GWAS signal is not a candidate-gene assignment.** ANKRD11, COX7C,
   and RPS15 lie in significant candidate windows, but a neighboring gene or a
   different regulatory target could explain the locus.
4. **Exact cell-type QTL data were sparse and underpowered.** The targeted QTL
   studies had 73 neurons, 104 microglial samples, or 211 bulk-neocortex
   samples. Bulk tissue can dilute cell-specific effects or reflect cell
   composition rather than regulation in astrocytes, OPCs, or inhibitory
   neurons.
5. **Some positive routes lacked the objects needed to test the primary
   shared-signal hypothesis.**
   APOE and RPS15 had both regional GWAS and eQTL signals, but complete fitted
   QTL models and source-matched LD were unavailable. These routes are
   unresolved, not failed colocalizations.
6. **Detected-event and significant-only releases cannot establish every
   negative.** Six sQTL routes lacked the target event in conditional/model
   files. Absence from those files does not prove that the event was measured
   and null.
7. **The phenotype and strata do not fully match Phase 18.** The main GWAS was
   an overall clinical-AD meta-analysis, while Phase 18 aggregated evidence
   originating from cell-, sex-, APOE-, and direction-specific transcriptomic
   contrasts. Phase 19 did not run formal variant-by-sex or variant-by-APOE
   interaction tests.
8. **The tested design emphasized common nuclear cis variation.** Complete
   rare-variant burden statistics were unavailable, and mtDNA variation was
   outside the nuclear analysis.
9. **Some QTL evidence reused ROSMAP.** NG00184 and positive ROSMAP sQTL tracks
   overlap the discovery cohort, making them mechanism/triangulation evidence
   rather than fully independent validation.

### 4.2 Plausible biological explanations, not demonstrated here

- A network key driver may be a downstream disease response, compensatory
  response, or stable module anchor rather than a germline susceptibility gene.
- Ribosomal and respiratory-chain genes may identify translation, stress, or
  oxidative-phosphorylation modules. Their network centrality need not be
  caused by local inherited regulation of the hub gene itself.
- Strong common regulatory variants in essential housekeeping genes may be
  constrained by selection, leaving effects that are rare, subtle, or acting
  through protein stability rather than steady-state RNA.
- The relevant mechanism may be trans regulation, a structural variant,
  rare coding variation, post-transcriptional control, protein abundance,
  somatic change, or a gene-by-environment interaction not captured by a
  conventional cis-QTL test.
- A driver may affect progression, pathology burden, resilience, or response
  after disease onset rather than case-control susceptibility. The completed
  CSF extension tested three useful endophenotypes, but it did not cover these
  other disease dimensions.
- Effects may exist only in a fine cell subtype, disease stage, sex/APOE group,
  or ancestry that was diluted in the available aggregate statistics.

Accordingly, failure to find common-variant support should lower confidence in
a simple germline cis-risk mechanism, but it does not refute a functional role
in established AD biology.

## 5. Limitations of the current approach

### 5.1 Scientific and design limitations

- **No primary multi-signal colocalization was resolved.** Across all Phase 19
  workstreams, the primary H0-H4 tables contain zero valid result rows. Signal
  proximity, PIP, and credible-set membership therefore remain descriptive.
- **Public releases were incomplete for primary multi-signal modeling.** The
  key gaps were full candidate-region QTL statistics, target-containing fitted
  SuSiE/LBF objects, exact variant order, and source/ancestry-matched LD.
- **The QTL cohorts were small and often context-mismatched.** Bulk neocortex is
  brain-relevant but cannot identify the cell type producing an association.
- **The discovery and validation cohorts were not always independent.** ROSMAP
  appears in NG00184 and in some positive RPS15 tracks; the CSF GWAS/QTL overlap
  audit also remains incomplete for several routes.
- **Ancestry coverage was narrow.** The principal GWAS and MAGMA analyses were
  European or European-dominant, and the planned LD panels were European/NHW.
  The conclusions may not transfer to other ancestries or LD structures.
- **The upstream `P < 5e-8` gate favors strong single-variant loci.** It is
  a conservative prespecified gate and can miss polygenic, allelic-heterogeneous,
  gene-based, interaction, rare-variant, or modest endophenotype mechanisms.
- **TWAS, GVC, and fine-mapping summary lists were incomplete evidence.**
  SELENOW lacked a model statistic, and APOE GVC membership lacked an effect,
  P value, variant mask, allele count, and replication result.
- **The evidence summaries emphasize significance and fine-mapping rather than
  harmonized effect magnitude.** Comparable gene-level effects and confidence
  intervals were not available across routes, so this report does not infer
  biological effect size or direction from P values alone.
- **The mitochondrial candidates were outside scope.** No mtDNA variants,
  heteroplasmy, haplogroup, copy number, depth, mitochondrial build, or NUMT
  controls were analyzed.
- **No independent functional validation was performed in Phase 19.** Genetic
  support and network causality are complementary but different questions.

### 5.2 Storage and access limitations

- Full NG00184 association archives were hundreds of gigabytes and failed the
  local storage contract; significant-only and fine-mapping summaries cannot
  always distinguish not measured from no signal.
- Richer FunGen-xQTL Synapse exports required access not available to the
  configured account. The open-source alternative was validated as a coverage
  audit, but `exact_source_reproduction = FALSE`.
- Controlled ADSP WGS, formal interaction analyses, and custom source-cohort
  LD were not available in the local public-data workflow.

### 5.3 Reproducibility and bundle-integrity caveats found during this summary audit

These issues do not change the reported gene-level conclusions, but they should
be repaired before describing the result bundles as fully reproducible:

1. [`tier2_prior_sensitivity.tsv.gz`](../../results/minerva_production/19_genetic_support_tier2_regional/tier2_prior_sensitivity.tsv.gz)
   and
   [`tier2_variant_harmonization.tsv.gz`](../../results/minerva_production/19_genetic_support_tier2_regional/tier2_variant_harmonization.tsv.gz)
   fail `gzip -t` with “unexpected end of file.” Their bytes match the artifact
   manifest and both are declared zero-row outputs, suggesting an empty-output
   writer/close bug. Hash validation alone did not test gzip structure.
2. The endophenotype execution report states that four complete NG00130.v2
   APOE CSF pQTL files were acquired, and downstream route/harmonization tables
   record their use. However, the individual raw files, URLs, sizes, and
   checksums are not enumerated in
   [`endophenotype_input_inventory.tsv`](../../results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension/endophenotype_input_inventory.tsv)
   or the published source checks.
3. Most large raw-source directories are ignored and are not present in this
   checkout. The published inventories preserve recorded paths and hashes, but
   the raw sources could not all be independently reopened during this audit.
4. The OPC/RPS15 execution report retains absolute `/home/...` paths from the
   original Linux execution host; the result manifests are mostly portable,
   but documentation links should use repository-relative paths.
5. The Tier 2 recovery
   [`analysis manifest`](../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_analysis_manifest.tsv)
   records 111,326 cases and 677,663 controls, whereas every row in
   [`recovery_regional_gwas_summary.tsv`](../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_regional_gwas_summary.tsv)
   records 85,934 cases and 401,577 controls. The encoded Bellenguez analysis
   sample and case fraction should be reconciled before any future custom
   case-control fine-mapping or colocalization run; no primary H0-H4 model was
   executed in the current recovery, so this inconsistency does not alter the
   reported zero-resolved-route result.
6. In
   [`endophenotype_prior_sensitivity.tsv.gz`](../../results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension/endophenotype_prior_sensitivity.tsv.gz),
   all nine sensitivity rows with signal ID `QTD000579` are labeled as sQTL
   routes. The eQTL Catalogue registry and route manifest identify `QTD000579`
   as the Walker bulk-neocortex **eQTL** dataset; `QTD000583` is the paired sQTL
   dataset. The numerical result summarized above is therefore interpreted as
   eQTL, but the modality and route IDs in this artifact should be corrected.

## 6. Recommended next work if more time and data are available

### 6.1 First repair the published evidence trail

1. Regenerate the two invalid zero-row gzip files with a properly closed writer
   and add `gzip -t` or equivalent decompression checks to bundle validation.
2. Add the four NG00130.v2 APOE pQTL source files to the input inventory and
   source checks with accession, resolved URL, size, MD5/SHA-256, build, allele
   convention, sample size, and acquisition date.
3. Replace execution-host absolute paths in documentation with portable
   repository-relative paths and document which raw inputs must be reacquired
   to reproduce each bundle.
4. Reconcile the Bellenguez case/control counts across the recovery analysis
   manifest, regional summaries, configuration, and source metadata before
   using the encoded case fraction in a future model.
5. Correct the `QTD000579` modality and route IDs in the endophenotype prior-
   sensitivity artifact, regenerate it from the frozen source tables, and add a
   registry-to-route consistency assertion to validation.

### 6.2 Highest-value scientific analyses

1. **Run candidate-frozen public brain/CSF pQTL, PWAS, and multi-model TWAS.**
   Screen all 19 nuclear genes, not only APOE. Require a cis-pQTL or reproducible
   prediction model for primary interpretation, perform conditional/fine-mapped
   analyses, and keep prediction-only associations suggestive until valid
   colocalization or high-PIP fine mapping supports them.
2. **Resolve APOE and RPS15 with complete signal-aware QTL packages.** Obtain
   full regional beta/SE/allele/frequency/sample-size statistics, the fitted
   SuSiE/fSuSiE alpha or LBF matrices, exact variant order/build, and
   source-cohort LD. Use `coloc.susie`, prior sensitivity, LD sensitivity, and
   conditional-signal analyses. Prefer independent or leave-ROSMAP-out sources.
3. **Use larger exact-cell-type eQTL/sQTL releases.** Prioritize OPC RPS15 and
   ANKRD11, inhibitory-neuron RPS15 and COX7C, and astrocyte APOE and COX7C.
   Audit donor overlap before calling a result independent validation.
4. **Run replicated rare-variant tests.** Use controlled WGS for prespecified
   loss-of-function, damaging-missense, and splice masks with burden tests and
   SKAT-O, ancestry-specific QC, and independent mask-level replication.
5. **Build a dedicated mtDNA workstream.** Analyze homoplasmic variants,
   heteroplasmy, haplogroup, mtDNA copy number, sequencing depth, contamination,
   NUMTs, mitochondrial reference build, and appropriate maternal/ancestry
   structure for the six mtDNA genes.
6. **Test the context that generated Phase 18 candidates.** Use formal
   SNP-by-sex and SNP-by-APOE interaction models, not differences in subgroup
   significance. If power permits, match QTL interactions to the same strata.
7. **Broaden AD phenotypes and ancestries.** Test age at onset, progression,
   cognitive decline, amyloid/tau PET, neuropathology, resilience, and larger
   multi-ancestry GWAS. Keep phenotype-specific conclusions separate from
   general AD-risk claims.
8. **Independently replicate and perturb the networks.** Replicate Phase 18 KDA
   in another cohort using expression-, degree-, and functional-class-matched
   nulls. For the most credible drivers, use graded perturbation, rescue, and
   target-module readouts to test network directionality directly.

## 7. Bottom line

Phase 19 provides a disciplined genetic annotation rather than broad genetic
validation of the Phase 18 list. It confirms **APOE** as strongly genetically
supported, retains **COX7C** and **SELENOW** as weak/suggestive, and identifies
**RPS15** as the most interesting unresolved non-APOE candidate. It does not
validate ANKRD11 or any other gene merely because a GWAS signal lies nearby.

For the remaining genes, “no support” has three distinct origins: a genuinely
signal-negative result under the tested common-variant thresholds, missing or
incompatible QTL/model/LD inputs, or a biological mechanism not represented by
the current nuclear cis-QTL design. The completed public-data workstreams are
technically informative, but `full_phase19_complete = FALSE` is the correct
status until mtDNA, rare-variant, interaction, independent QTL, and valid
multi-signal colocalization routes are addressed.

## 8. Primary evidence files

### Documentation

- [Overall Phase 19 roadmap](overall_plan.md)
- [Tier 1 execution report](tier1/tier1_execution_report.md)
- [Tier 2 regional execution report](tier2/tier2_execution_report.md)
- [Tier 2 recovery execution report](tier2/tier2_recovery_execution_report.md)
- [APOE/RPS15 unresolved colocalization explanation](tier2/apoe_rps15_unresolved_colocalization_explained.md)
- [Endophenotype extension execution report](endophenotype_gwas_qtl_extension/endophenotype_gwas_qtl_extension_execution_report.md)
- [OPC/RPS15 public recovery execution report](opc_rps15/opc_rps15_public_data_first_execution_report.md)

### Results

- [Tier 1 candidate manifest](../../results/minerva_production/19_genetic_support_tier1/genetic_support_candidate_manifest.tsv)
- [Tier 1 evidence summary](../../results/minerva_production/19_genetic_support_tier1/genetic_support_evidence_summary.tsv)
- [Tier 2 recovery route decisions](../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_route_decisions.tsv)
- [Tier 2 recovery regional-GWAS summary](../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_regional_gwas_summary.tsv)
- [Tier 2 recovery regional-QTL summary](../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_regional_qtl_summary.tsv)
- [CSF endophenotype evidence summary](../../results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension/endophenotype_evidence_summary.tsv)
- [CSF gate decisions](../../results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension/endophenotype_gate_decisions.tsv)
- [RPS15 public-recovery evidence summary](../../results/minerva_production/19_genetic_support_opc_rps15_public_recovery/opc_rps15_evidence_summary.tsv)
- [RPS15 route audit](../../results/minerva_production/19_genetic_support_opc_rps15_public_recovery/opc_rps15_qtl_audit.tsv)
