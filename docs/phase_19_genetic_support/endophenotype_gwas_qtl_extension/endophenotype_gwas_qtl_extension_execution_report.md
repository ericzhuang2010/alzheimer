# Phase 19 Endophenotype GWAS/QTL Extension Execution Report

**Execution status:** validated complete  
**Completed:** 2026-08-21  
**Execution stage:** local production-equivalent  
**Backend:** direct local execution; Minerva was not used  
**Published bundle:** `results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension/`  
**Validation status:** `validated_complete_endophenotype_gwas_qtl_extension`

## Executive outcome

The plan was executed for all 25 frozen ROSMAP Phase 18 genes, all 47 frozen
candidate contexts, and the three preregistered CSF Alzheimer endophenotypes.

Only **APOE** passed either GWAS follow-up gate. APOE passed both the regional
genome-wide-significance gate and the candidate-frozen MAGMA gate for
amyloid-beta 42, total tau, and p-tau181. The other 18 nuclear genes had no
qualifying signal for any biomarker under the frozen thresholds.

The extension added **zero newly biomarker-supported genes** under the
preregistered strong/moderate definition. APOE has strong biomarker-region and
gene-based statistical association, but no route supplied a compatible
multi-signal QTL model or ancestry-matched QTL LD that could establish a
shared causal GWAS/QTL signal. APOE therefore receives weak,
biomarker-specific statistical support from this extension, not a new
gene-level validation.

This distinction matters: the data strongly implicate the APOE region in all
three biomarkers, but the completed analysis cannot yet show that the DNA
variant or signal changing the biomarker is the same signal changing APOE
expression, splicing, or protein abundance.

## Frozen scope and accounting

The execution reproduced the preregistered scope without adding candidates
after viewing the GWAS results:

| Unit | Observed |
|---|---:|
| Frozen unique genes | 25 |
| Nuclear genes | 19 |
| mtDNA genes | 6 |
| Candidate-context rows | 47 |
| Biomarkers | 3 |
| Unique gene-biomarker units | 75 |
| Nuclear gate decisions | 57 |
| mtDNA not-applicable gene-biomarker rows | 18 |
| Candidate-context-biomarker rows | 141 |
| mtDNA context-biomarker not-applicable rows | 60 |

All 57 nuclear decisions are terminal. The six mtDNA genes remain explicit
`not_applicable_mtdna` rows and were not treated as negative nuclear cis-QTL
results.

The frozen pre-QTL decision file is:

`data/reference/phase19_genetic_support/endophenotype_gwas_qtl_extension/source_manifest/endophenotype_pre_qtl_gate_decisions.tsv`

Its SHA-256 is
`425d618d1c2b68099264ebeb5896122e04f161ad0c438eb4352b0822b2c8427c`.

## Primary GWAS acquisition and QC

The primary European-ancestry meta-analysis files were downloaded from the
official GWAS Catalog release and mapped by trait metadata rather than
accession order.

| Trait | Accession | Sample size | Valid autosomal rows | Invalid rows | Candidate regions passing coverage |
|---|---|---:|---:|---:|---:|
| CSF amyloid-beta 42 | `GCST90726396` | 18,948 | 7,345,582 | 0 | 19/19 |
| CSF total tau | `GCST90726397` | 18,948 | 7,346,530 | 0 | 19/19 |
| CSF p-tau181 | `GCST90726398` | 18,948 | 7,396,296 | 0 | 19/19 |

Raw MD5 checksums were:

| Accession | Raw MD5 |
|---|---|
| `GCST90726396` | `4cb99e5a870ebf9d6f0d9601f4bbee08` |
| `GCST90726397` | `e54e8dd64b2c9fc8893ddf04f0be5716` |
| `GCST90726398` | `e867ec48c1a490be5613746f70a557a8` |

The normalized source identities, URLs, coordinate/effect conventions, and
hashes are preserved in
`endophenotype_biomarker_manifest.tsv` and
`endophenotype_input_inventory.tsv` in the published bundle.

## GWAS and MAGMA results

The gate produced 54 `no_qualifying_gwas_signal` decisions and three
`regional_and_gene_based_signal` decisions. All three positive decisions are
APOE:

| Biomarker | APOE regional minimum P | Gene-body MAGMA P | +/-10 kb MAGMA P |
|---|---:|---:|---:|
| CSF amyloid-beta 42 | numerical underflow to 0 | `5e-10` | `2.3037e-14` |
| CSF total tau | `5.4e-161` | `5e-10` | `1.2218e-13` |
| CSF p-tau181 | `3.27e-174` | `5e-10` | `5e-10` |

The amyloid-beta value reported as zero is numerical p-value underflow, not a
literal probability of zero.

MAGMA v1.10 used the official Phase 3 European reference with dbSNP151
synonyms and the Ensembl v110 GRCh37 gene-location file. The gene-body primary
analysis and +/-10 kb sensitivity were run and stored separately. APOE remains
significant in both. SNP-level conditional MAGMA was not run because no
preregistered independent-variant conditioning model was available; that
limitation is explicit in `endophenotype_magma_conditional.tsv`.

## Molecular-QTL acquisition

Candidate-specific molecular-QTL acquisition began only after the 57-row gate
was frozen.

### CSF pQTL

Four complete APOE CSF pQTL summary-statistic files from `NG00130.v2` were
obtained and checksum-verified:

- total apolipoprotein E, `GCST90424891`;
- APOE E3, `GCST90425531`;
- APOE E4, `GCST90425532`; and
- APOE E2, `GCST90426314`.

### ADSP FunGen xQTL Atlas

The public `NG00184.v1` release was inventoried result-blind. The complete
bulk eQTL and single-nucleus eQTL `all` archives exceeded the preregistered
local storage gate, so they were not downloaded. Instead, the released
HMT-significant and single-context fine-mapping archives were acquired for the
four relevant modalities:

- eQTL HMT-significant and fine-mapping;
- pQTL HMT-significant and fine-mapping;
- sQTL HMT-significant and fine-mapping; and
- single-nucleus eQTL HMT-significant and fine-mapping.

The eight archives total 4,197,416,960 bytes. All eight matched the official
NIAGADS MD5 values. Only chromosome 19 files were extracted for the frozen
APOE audit. The official metadata JSON was also checksum-verified. The final
input inventory contains the eight archives plus metadata, with both official
MD5 validation state and locally recomputed SHA-256.

Context filtering used the official `cell type`, `Biosample type`, and
`Tissue category` fields. Microglial and monocyte signals were not promoted
to the registered astrocyte route.

The context-eligible APOE audit found:

| Modality | HMT-significant APOE rows | Fine-mapping APOE rows | Maximum released PIP | Route conclusion |
|---|---:|---:|---:|---|
| Bulk-brain eQTL fallback | 0 | 44 | 0.1512 | Measured; no source-significant signal |
| Brain pQTL | 0 | 22 | 0.7606 | Measured; no source-significant signal |
| Bulk-brain sQTL fallback | 189 | 245 | approximately 1.0 | Source-significant signal; model/LD incompatible |
| Astrocyte single-nucleus eQTL | 0 | 8 | 0.2163 | Measured; no source-significant signal |

For eQTL, pQTL, and astrocyte single-nucleus eQTL, the released APOE
fine-mapping records explicitly have `is_hmt_signif=false`. This supports a
“measured but no source-significant signal” conclusion rather than treating
absence from a significant-only table as proof of no QTL.

For sQTL, the source-significant bulk-brain signal is real and promising.
However, the released fine-mapping table contains PIP, conditional-effect, and
credible-set membership summaries—not the complete SuSiE signal model,
variant-by-signal posterior matrix, or source/ancestry-matched LD required for
primary multi-signal colocalization. PIP or credible-set overlap alone was not
used as H4 evidence.

## QTL-route terminal results

The frozen APOE-positive set generated 27 routes: nine registered routes for
each of the three biomarkers.

| Terminal status | Routes |
|---|---:|
| `model_or_ld_incompatible` | 9 |
| `no_regional_qtl_signal` | 9 |
| `not_assessable` | 9 |
| Total terminal routes | 27 |

The nine model/LD-incompatible routes are:

- three `NG00130.v2` CSF pQTL routes;
- three EQTL Catalogue bulk-neocortex eQTL routes; and
- three `NG00184.v1` bulk-brain sQTL routes.

The nine no-signal routes are the three-biomarker combinations of
`NG00184.v1` brain pQTL, bulk-brain eQTL, and astrocyte single-nucleus eQTL.

The remaining nine routes are explicit unassessable states for EQTL Catalogue
sQTL, scMetaBrain eQTL, and PsychAD single-nucleus eQTL. No missing route was
silently dropped.

`NG00184.v1` includes ROSMAP-derived data, and the positive sQTL route is
ROSMAP bulk brain. Even a future resolved colocalization from this route would
initially be mechanism/triangulation evidence, not fully independent
validation, unless replicated in an independent or leave-ROSMAP-out source.

## Single-signal sensitivity analyses

Forty-five `coloc.abf` sensitivity rows were retained: five APOE molecular
traits, three biomarkers, and three frozen `p12` values.

At the primary `p12=5e-6`, the total APOE CSF pQTL comparison had
`PP.H4 approximately 0.999638` for all three biomarkers. The bulk-neocortex
APOE eQTL comparison instead favored distinct signals, with
`PP.H3 approximately 0.99053` and `PP.H4 approximately 0.000345`.

These values are labeled `not_graded_sensitivity_only`. APOE is a
multi-signal locus, and neither QTL route supplied the complete primary
multi-signal model/LD contract. The attractive CSF pQTL H4 therefore did not
upgrade APOE.

No `coloc.susie` result was fabricated from PIP summaries, incomplete
statistics, or a substitute LD panel.

## Evidence integration

The extension result is:

`newly_biomarker_supported_unique_genes = 0`

APOE receives weak extension evidence because it passes corrected MAGMA and
regional GWAS gates. It does not receive moderate or strong biomarker-specific
shared-signal support. No prior Phase 19 cumulative grade was downgraded.

Permitted wording:

> The APOE region has strong statistical association with CSF amyloid-beta 42,
> total tau, and p-tau181. Available molecular-QTL results are biologically
> suggestive, especially CSF APOE protein and bulk-brain APOE splicing, but the
> current releases do not establish a shared multi-signal causal variant.

Not permitted:

> APOE was newly validated by QTL colocalization for all three biomarkers.

## Local execution details

The run used:

- Linux 7.0.0-29-generic, x86-64;
- Python 3.12.3;
- R 4.3.3;
- MAGMA 1.10;
- 15 GiB physical RAM plus 4 GiB swap;
- direct local backend, one analysis worker; and
- 386 GiB free disk after acquisition and publication, above the 50 GiB
  reserve.

No GPU and no Minerva job were used. No primary QTL fine-mapping job was
started after the model/LD gates failed, so the 9 GiB local per-locus ceiling
was not approached.

Principal safe commands were:

```bash
python3 scripts/19_run_endophenotype_extension.py --gate-only
python3 scripts/19_prepare_endophenotype_magma.py
python3 scripts/19_analyze_endophenotype_apoe_qtl.py
python3 scripts/19_audit_ng00184_apoe.py

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/phase19_endophenotype_local_execution.yml \
  --phase genetic_support_endophenotype \
  --force

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  scripts/19_validate_endophenotype_extension.py

PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_phase19_endophenotype_extension
```

The public atlas downloads used NIAGADS file IDs `57057`, `57059`,
`57087`, `57089`, `57097`, `57099`, `57107`, and `57109`, with a
maximum of two simultaneous downloads. Resolved source URLs and all checksums
are recorded in local source manifests and the published inventory. No
credential, signed URL, cookie, or authorization header is recorded in this
report or the result bundle.

## Validation and publication

The final bundle contains exactly 36 declared files and no undeclared
sidecars. The output-only validator independently reproduced:

```text
validated_complete: files=36 artifacts=34 gates=57 routes=27 matrix_rows=141 credential_patterns=0
```

The extension regression suite completed seven tests successfully. The
inherited Phase 19 recovery pilot also passed 14 synthetic controls covering
shared and distinct signals, allele flipping, LD symmetry/diagonal/PSD/order,
and ancestry rejection. The inherited Tier 2 multi-signal pilot independently
converged on its SuSiE fixtures and passed harmonization, LD-order, parser, and
exact pilot-output checks.

All published blocking checks are `pass`. The independent validator recomputed all 34
artifact SHA-256 values, the artifact-manifest digest, key row counts, terminal
route states, atlas MD5 validation records, and credential-leak patterns.

Final status:

| Field | Value |
|---|---|
| Technical status | `validated_complete` |
| Baseline Phase 19 hashes unchanged | `TRUE` |
| Blocking failures | 0 |
| Declared files | 36 |
| Undeclared files | 0 |
| Full Phase 19 complete | `FALSE` |
| Newly biomarker-supported genes | 0 |

The `full_phase19_complete=false` value is intentional. This extension is
technically complete, but broader Phase 19 remains open to future independent
QTL models, author-provided LD, and other prespecified validation routes.

## Best remaining data request

The highest-value next request is not another significant-variant table. It is
a complete, signal-aware APOE sQTL package from an independent brain cohort,
or a leave-ROSMAP-out release, containing:

1. full candidate-region beta, standard error, alleles, frequency, and sample
   size;
2. the complete SuSiE/fSuSiE fitted signal object or alpha/log-Bayes-factor
   matrices;
3. exact variant order and build;
4. ancestry- and source-matched LD or a documented genotype-derived LD
   procedure; and
5. cohort-overlap metadata.

That package would directly address the remaining sQTL
`model_or_ld_incompatible` state. Until then, the honest scientific result is
zero newly validated genes, with APOE remaining the only biomarker-associated
candidate and the main unresolved mechanistic locus.
