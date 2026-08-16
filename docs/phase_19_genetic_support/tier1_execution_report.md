# Phase 19 Tier 1 execution report

## Outcome

Tier 1 was executed locally on 2026-08-16 for all 25 Phase 18 genes in all 47
selected gene × broad-cell-type × driver-class units. The validated output is:

```text
results/minerva_production/19_genetic_support/
```

The run completed the 23-file Tier 1 output contract. It is technically
complete for Tier 1, but it is not marked as full Phase 19 completion because
the public source does not contain classical colocalization H0-H4 posteriors,
a complete rare-variant burden table, or mtDNA-specific association results.

## Frozen inputs

- Phase 18 source: `call_key_driver_returns.tsv`, SHA-256
  `b917f70e6edcdf030f63e88ba8fbc5b22b80714599c12c80ea449e8c38bd51d8`.
- Candidate rule: unique `key_driver + broad_network + case_id` among rows with
  `top5_display = TRUE`.
- Scope recovered from the source: 47 candidate-context units, 25 genes, 19
  nuclear genes, and 6 mtDNA genes.
- Gene coordinates: GENCODE v44 basic, GRCh38.
- Gene-symbol validation: HGNC complete set dated 2026-06-05.
- Genetics source: official [FunGen-xQTL public GitHub snapshot](https://github.com/statfungen/xqtl-resources) at commit
  `f6f63fc319a417213cf1e86ec0eb14fcb53d2427` (2026-07-29).
- Download size: approximately 8.7 MB across six checksum-frozen public source
  files. No individual-level genotype or phenotype data were downloaded.

The external source files and their checksums are recorded in:

```text
data/reference/phase19_genetic_support/source_manifest.tsv
```

## Tier 1 method

The workflow reconstructed the candidate list from Phase 18, mapped every gene
to a GRCh38 locus, screened the official unified AD fine-mapping/xQTL tables
within a ±1 Mb window, extracted direct candidate-gene mappings, checked the
release TWAS and GVC companion gene lists, recorded route-level assessability,
and generated a matrix plus two locus-review pages.

The public FunGen-xQTL fields named inclusion score, VCP, confidence level, or
CL1-CL6 were preserved under their source names. They were not renamed as
classical coloc `PP.H4`. All H0-H4 output columns are explicitly missing, and
the QC table explains why.

## Results

The 47 candidate-context results have these Tier 1 grades:

| Grade | Candidate-context units | Meaning in this run |
|---|---:|---|
| Strong | 1 | APOE in the Phase 18 astrocyte network; direct genome-wide AD fine-mapping support including rs429358, with functional evidence only in fallback brain contexts. |
| Moderate | 0 | No candidate met the frozen moderate rule. |
| Weak | 3 | COX7C in astrocyte and inhibitory-neuron networks, plus SELENOW in the excitatory-neuron network. Context or source-statistic limitations prevent a higher grade. |
| None found | 23 | No direct candidate mapping occurred in the registered filtered Tier 1 summary. This does not mean that genetic evidence is absent. |
| Not assessable | 20 | The six mtDNA genes across 20 Phase 18 contexts require mtDNA-specific resources absent from this Tier 1 source. |

Key qualifications:

- APOE: rs429358 is reported in the source with AD fine-mapping inclusion score
  1.0 and minimum reported GWAS P approximately `1.88e-155`. The xQTL/TWAS
  context is a fallback brain context, not an exact astrocyte result.
- COX7C: the public entry is a bulk sQTL CL5 result at rs2010322. Its AD P value
  is approximately `2.64e-6` and xQTL inclusion score approximately `0.026`, so
  it is weak/suggestive rather than genome-wide support.
- SELENOW: it appears in the public TWAS gene list, but the companion list does
  not provide a model-level statistic or exact excitatory-neuron context.
- APOE also appears in the ADSP GVC companion list, but that list provides gene
  membership rather than a burden-test effect, P value, mask, or replication
  result. It was therefore not treated as a positive rare-variant test.

## Validation

All 11 registered checks passed or produced the expected nonblocking Tier 1
limitation. The output contains exactly 47 evidence-summary rows, 25 unique
genes, 188 route-assessability rows, and 23 declared files. The automated test
suite passed:

```text
3 passed
```

The test suite performs a fresh end-to-end build in a temporary directory,
checks scope and uniqueness, verifies that H0-H4 remain unavailable, and
recomputes every declared artifact hash.

## Files added or changed

Added:

- `config/phase19_genetic_support.yml`
- `config/phase19_local_production_execution.yml`
- `requirements/phase19_genetic_support.txt`
- `scripts/19_run_genetic_support.py`
- `tests/test_phase19_genetic_support.py`
- this execution report
- the 23-file validated result bundle

Changed:

- `.gitignore`
- `scripts/run_pipeline.R`
- `config/minerva_shared.yml`
- workstation-only `config/local_pilot.yml`
- `docs/phase_19_genetic_support/human_genetic_support_plan.md`

Deleted: none.

## Reproduction

The tested local command is:

```bash
.venv/bin/python scripts/19_run_genetic_support.py \
  --config config/phase19_genetic_support.yml \
  --execution-config config/phase19_local_production_execution.yml \
  --task-mode genetic_support
```

The task is also registered as global pipeline mode `genetic_support`. The
repository's current local R/renv activation has a pre-existing offline lock /
Bioconductor-validation issue, so the Python command above was used for this
execution and is the locally tested route.

## Decision after Tier 1

Tier 1 is sufficient for a screened, auditable human-genetics annotation of
all Phase 18 candidates. Tier 2 is needed only if the study must make classical
signal-level colocalization claims, perform full corrected rare-variant burden
comparisons, or evaluate the six mtDNA genes with heteroplasmy/haplogroup/
copy-number-aware data. Those are the main missing evidence routes; running the
same Tier 1 screen on Minerva would not fill them.
