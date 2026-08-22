# Phase 19 Tier 2 Classical Colocalization Recovery Execution Report

## Outcome

The recovery plan was executed locally on homedesktop on 2026-08-21. No
Minerva compute was used. The validated bundle was published atomically to:

~~~text
results/minerva_production/19_genetic_support_tier2_recovery/
~~~

The terminal status is:

~~~text
validation_status = validated_complete_tier2_classical_coloc_recovery
execution_stage = local_production_equivalent
execution_backend = direct
candidate_contexts = 47
nuclear_recovery_routes = 54
terminal_recovery_routes = 54
blocking_check_failures = 0
declared_output_files = 26
full_phase19_complete = FALSE
~~~

The recovery made the previous generic 54-route not_assessable result more
specific:

| Terminal state | Routes | Meaning |
|---|---:|---|
| no_regional_gwas_signal | 42 | The complete dense Bellenguez candidate region had no variant below the frozen 5e-8 GWAS gate. |
| no_regional_qtl_signal | 4 | Complete indexed eQTL statistics were present, but the gene did not pass the frozen per-gene 0.05 / tested-variants regional signal gate. |
| model_or_ld_incompatible | 2 | Dense eQTL signal was present, but the source SuSiE model was absent and QTL-ancestry-matched LD was unavailable. |
| not_assessable | 6 | The target splicing event was absent from the conditional-statistics and released-model files; this does not prove it was measured and had no signal. |

No route had both a compatible GWAS signal model and a compatible released QTL
signal model. Therefore, zero H0-H4 posterior rows were calculated. This is a
scientific input-gate result, not a software failure and not evidence that
colocalization is absent.

## Data acquired and extracted

The run acquired and checksum-registered 19 public source files totaling
2,959,598,125 bytes:

- pinned eQTL Catalogue r7 metadata at commit
  10966d360a4394c16e338fb9345ec71f4cd5b1fa;
- six released SuSiE LBF archives and six credible-set archives;
- three released LeafCutter conditional-statistics/event-mapping archives; and
- the NIAGADS NG00067.v21 public file registry.

The source directory occupies about 2.8 GiB:

~~~text
data/reference/phase19_genetic_support/tier2_recovery/
~~~

Because the released SuSiE archives omitted all target traits, the run then used
direct FTP tabix range access to the official complete indexed eQTL files. It
extracted 62,551 candidate-gene regional rows into two deterministic local
files and pinned both official tabix indexes by SHA-256. It did not download
the whole dense eQTL archives.

The six dense eQTL gates were:

| Dataset/context | Gene | Rows | Minimum P | Frozen threshold | Signal |
|---|---|---:|---:|---:|---|
| Aygun neuron | RPS15 | 9,931 | 1.93132e-4 | 5.03474e-6 | No |
| Aygun neuron | COX7C | 7,061 | 9.24749e-4 | 7.08115e-6 | No |
| Walker neocortex | RPS15 | 13,302 | 2.11971e-6 | 3.75883e-6 | Yes |
| Walker neocortex | COX7C | 9,677 | 2.58275e-3 | 5.16689e-6 | No |
| Walker neocortex | APOE | 11,522 | 9.51257e-8 | 4.33952e-6 | Yes |
| Walker neocortex | ANKRD11 | 11,058 | 1.81941e-4 | 4.52161e-6 | No |

The two dense signals are the APOE astrocyte/bulk-neocortex fallback eQTL route
and the RPS15 OPC/bulk-neocortex fallback eQTL route. They were not forced into
colocalization because the released source SuSiE models omit those genes and
the source study's compatible QTL LD was not available.

## LD decision

The ADSP R5 non-Hispanic White LD sources were registered before results were
inspected. Partial chromosome transfers were started while the QTL archives
were being acquired. Once the complete QTL audit showed that no route had a
compatible released QTL signal model, the prespecified upstream gate stopped LD
processing. The incomplete LD files were removed and were never registered or
used as inputs.

Four explicit LD decision rows record:

~~~text
extraction_state = not_required_after_qtl_model_gate
reason = no_released_qtl_susie_signal_model_and_no_qtl_ancestry_matched_ld_for_dense_signals
~~~

This follows the plan's rule that ancestry-matched LD is acquired and modeled
only after both upstream signal/model gates pass. ADSP GWAS LD alone cannot
replace ancestry-compatible LD for the QTL study.

## Local pilot and validation

The local pilot passed 14 checks, including deterministic synthetic shared- and
distinct-signal controls, allele flipping, LD order/symmetry/diagonal/PSD
checks, ancestry rejection, exact route construction, and immutable baselines.

The production bundle passed all 12 blocking checks. Final verification also
confirmed:

~~~text
Tier 1 artifact hashes unchanged = TRUE
Tier 2 artifact hashes unchanged = TRUE
recovery artifact hashes reproduced = 24 / 24
output files = 26 / 26
undeclared recovery output files = 0
credential material found = FALSE
~~~

The artifact manifest excludes itself and the status file to avoid circular
hashes, matching the existing Phase 19 convention.

## Code and reproducibility

Recovery-specific implementation:

~~~text
config/phase19_genetic_support_tier2_recovery.yml
config/phase19_tier2_recovery_local_execution.yml
scripts/19_inventory_tier2_recovery_sources.py
scripts/19_download_tier2_recovery_qtl.py
scripts/19_extract_tier2_recovery_qtl_models.py
scripts/19_extract_tier2_recovery_dense_qtl.py
scripts/19_prepare_tier2_recovery_ld.py
scripts/19_run_genetic_support_tier2_recovery.R
tests/test_phase19_genetic_support_tier2_recovery.R
tests/fixtures/phase19_tier2_recovery/
~~~

The task is registered as genetic_support_tier2_recovery in the shared local
dispatcher. The production-equivalent command was:

~~~bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/phase19_tier2_recovery_local_execution.yml \
  --phase genetic_support_tier2_recovery
~~~

## Remaining scientific fixes

Two distinct access gaps remain:

1. For APOE and bulk-neocortex RPS15 eQTL, obtain a complete source SuSiE/LBF
   model that includes the gene, or obtain source-study ancestry-matched LD and
   full covariate-compatible statistics for a custom QTL fine-map.
2. For the six sQTL routes, obtain a complete all-tested-event release plus a
   measurement/annotation manifest. The current conditional-statistics files
   include detected events only, so absence cannot be changed to
   no_regional_qtl_signal.

If either source becomes available, the frozen route, context, prior, signal,
and compatibility rules can be rerun without changing the two baseline bundles.
