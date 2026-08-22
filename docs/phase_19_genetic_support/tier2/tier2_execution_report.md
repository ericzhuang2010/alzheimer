# Phase 19 Tier 2 execution report

Execution date: 2026-08-21  
Execution host: `homedesktop`  
Execution backend: local direct execution  
Canonical results: `results/minerva_production/19_genetic_support_tier2_regional/`

Path-only migration (2026-08-21): this directory was renamed from
`results/minerva_production/19_genetic_support_tier2/` by adding the
`_regional` suffix. No scientific analysis was rerun, and all 23 regional
result-file contents and their recorded artifact hashes were unchanged.

## Outcome

The approved open-data alternative was executed locally without Minerva. The
registered pipeline published the complete 23-file contract atomically and all
blocking source, scope, output, and artifact checks passed.

```text
validation_status = validated_complete_tier2_regional_coloc
technical_status = validated_complete_tier2
scientific_status = tier2_open_alternative_complete_classical_coloc_not_assessable
blocking_check_failures = 0
exact_source_reproduction = FALSE
full_phase19_complete = FALSE
```

This is a technically complete Tier 2 regional source/model audit, not a
positive or negative classical colocalization result. None of the 54 routes
had a compatible classical H0-H4 result or the complete dense QTL/model/LD
combination required for a valid custom analysis. All 54 therefore end
`not_assessable`; no Phase 19 evidence grade changed.

## Public data acquired

The ignored local source tree is
`data/reference/phase19_genetic_support/tier2/` and occupies about 1.9 GB.
The final source manifest contains 33 records: 11 required immutable files,
three registered deferred sources, and 19 candidate-gene coverage queries.

| Source | Acquired content | Integrity/result |
|---|---|---|
| NIAGADS `NG00184.v1` eQTL | `single_context_finemapping_all`, 365,291,520 bytes | MD5 `cb06f0fded0879612fa534066b255e63` passed |
| NIAGADS `NG00184.v1` sQTL | `single_context_finemapping_all`, 563,374,080 bytes | MD5 `c1e0c85799b027849fbe64496d7ef326` passed |
| NIAGADS `NG00184.v1` snuc-eQTL | `single_context_finemapping_all`, 313,733,120 bytes | MD5 `f0d3457b1ed556f85cfbc2651a20190f` passed |
| NIAGADS metadata/manifests | metadata JSON/text, three child manifests, combined manifest | All frozen byte and MD5 gates passed |
| NIAGADS gene endpoint | one significant-only table for each of 19 nuclear candidates | 19/19 valid tables; coverage screening only |
| GWAS Catalog `GCST90027158` | full GRCh38 Bellenguez 2022 statistics, 755,201,909 bytes | MD5 `9d23b9ba23532da38ab83fb061bab18f` passed |
| GWAS Catalog checksum | official `md5sum.txt` | Frozen and verified |

The complete NG00184 association archives were not downloaded: together they
are approximately 821 GB and fail the local storage contract. Significant-only
gene-query rows were never used as dense custom-coloc input.

## Deterministic candidate extraction

Source archives were not unpacked recursively. The extraction utility streamed
the immutable archives and full GWAS and retained only the frozen Phase 19
candidate genes/regions.

| Derived input | Coverage | Reproduced SHA-256 |
|---|---:|---|
| `ng00184_candidate_qtl_finemapping.tsv.gz` | 9,363 rows, all 19 nuclear genes | `0013af5b06df5655f5a87167f4b141a85c23aa241026979f75119db06ad5b595` |
| `bellenguez_candidate_gwas.tsv.gz` | 311,180 unfiltered regional rows, all 19 nuclear genes | `25eaf3646f105ab59017cc38fd34eaf01a326ee4fd411f405b53c3882e8e4bd6` |

Each GWAS locus contains 13,612 to 23,085 variants. Four candidate-gene windows
contain a variant with `p < 5e-8`; this is only regional signal coverage and is
not a gene-level causal assignment. The gzip writer fixes `mtime=0`; a complete
second extraction reproduced both SHA-256 values exactly.

The QTL extract contains:

- 2,696 bulk eQTL fine-mapping rows;
- 1,473 single-nucleus eQTL fine-mapping rows;
- 5,194 sQTL fine-mapping rows; and
- 1,418 rows assigned to a released 95% credible set.

## Route-level scientific outcome

The frozen scope reproduced 47 candidate contexts, 25 genes, 19 nuclear genes,
27 nuclear contexts, 20 mtDNA contexts, and exactly 54 nuclear eQTL/sQTL routes.

| Terminal outcome | Routes |
|---|---:|
| Released QTL fine mapping present, but matching AD H0-H4 or valid custom inputs absent | 52 |
| Released candidate QTL fine mapping absent | 2 |
| Classical precomputed H0-H4 resolved | 0 |
| Custom coloc resolved | 0 |
| Total `not_assessable` | 54 |

Among the 52 routes with released QTL fine-mapping coverage, 24 used an exact
cell context and 28 used the prespecified bulk-brain fallback. Twenty-two routes
contained at least one released CS95 row. The two uncovered routes are LAMTOR5
sQTL in excitatory and inhibitory neurons.

No ancestry-matched LD block was downloaded because no route passed the prior
full-regional-QTL/model gate for a custom run. Downloading ADSP or 1000 Genomes
LD anyway would not make a valid colocalization and would violate the plan's
result-blind acquisition order. Those panels remain registered for a later
candidate-specific custom analysis.

## Validation

- The immutable Tier 1 artifact hashes reproduced before and after execution.
- All 11 required alternative source files passed frozen byte/MD5 checks.
- The deterministic two-signal SuSiE/coloc smoke test recovered two shared and
  two distinct signal pairs.
- The Tier 2 regression suite passed against the real public files.
- All 54 routes have terminal states and all 47 cumulative summary rows are
  present, including 20 mtDNA `not_applicable_mtdna` rows.
- The final directory contains exactly 23 declared files.
- All 21 artifact-manifest entries reproduce their SHA-256 values.
- Final artifact-manifest SHA-256:
  `6b0042c3e78b35385aaab541fa40c10d8ccb6daf1e46edba245085de64ba6524`.

The core commands were:

```bash
python3 scripts/19_download_genetic_support_tier2_alternative.py
python3 scripts/19_extract_genetic_support_tier2_alternative.py
Rscript tests/test_phase19_genetic_support_tier2.R
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/phase19_tier2_local_execution.yml \
  --phase genetic_support_tier2
```

## Exact-source sensitivity and remaining scope

The FunGen-xQTL Synapse entities remain unreadable by the configured account.
They are now an optional exact-source sensitivity, not a prerequisite for the
validated open-data bundle. The production manifest explicitly records
`exact_source_reproduction = FALSE`.

A later classical-colocalization increment would need targeted dense regional
QTL statistics, a matching fine-mapping model or a justified custom model, and
ancestry-compatible LD for the same ordered variants. It must create new route
results without relabeling this fine-mapping coverage audit as H4 evidence.
Rare-variant and mtDNA analyses remain separately scoped, so
`full_phase19_complete` correctly remains false.
