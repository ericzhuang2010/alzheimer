# Phase 08 broad-cell DEG local pilot results

## Outcome

The Vasculature local pilot completed on 2026-08-28 with final status
`validated_complete`. It reused the validated Phase 07 donor-by-fine-cell raw
count bundle and did not change or rerun an earlier phase.

The pilot produced all six structural Vasculature result sets. Four were
estimable under the frozen primary gates; two e2 sets were retained as explicit
empty files with `not_estimable` statuses because they had fewer than five
eligible donors in at least one disease arm.

| Group | Eligible AD/NCI donors | Terminal status | Tested genes | Strict DEGs | Relaxed DEGs | Exploratory DEGs |
|---|---:|---|---:|---:|---:|---:|
| `F_e2` | 3 / 10 | `not_estimable` | 0 | 0 | 0 | 0 |
| `F_e33` | 29 / 35 | `validated_complete` | 8,096 | 2 | 2 | 2 |
| `F_e4` | 19 / 9 | `validated_complete` | 8,096 | 3 | 5 | 7 |
| `M_e2` | 4 / 3 | `not_estimable` | 0 | 0 | 0 | 0 |
| `M_e33` | 20 / 39 | `validated_complete` | 8,096 | 2 | 2 | 2 |
| `M_e4` | 21 / 6 | `validated_complete` | 8,096 | 0 | 0 | 3 |
| **Total** | — | 4 complete / 2 not estimable | **32,384** | **7** | **9** | **14** |

Every completed full result contains both positively signed (AD-up) and
negatively signed (AD-down) tested genes. A thresholded direction is allowed to
contain zero DEGs; for example, the relaxed `F_e33` calls are both AD-down, while
the relaxed `M_e33` calls are both AD-up.

The relaxed tier contains nine DEG rows. One is a core-mito gene, `HIBCH`, in
the `F_e4` AD-down result. The core-mito handoff contains three rows because the
same gene/category is represented in the strict, relaxed, and exploratory
signature tiers. This phase makes no key-driver calls.

## Composition sensitivity

The diagnosis-blind fine-type composition sensitivity used a 0.5-nucleus zero
pseudocount, centered-log-ratio fine-type proportions, and two PCs. It completed
the same four supported contrasts and retained the same two unsupported e2
contrasts.

| Group | Primary/sensitivity logFC correlation | Sign concordance | Primary relaxed DEGs | Sensitivity relaxed DEGs |
|---|---:|---:|---:|---:|
| `F_e33` | 0.916 | 0.915 | 2 | 2 |
| `F_e4` | 0.966 | 0.961 | 5 | 2 |
| `M_e33` | 0.972 | 0.962 | 2 | 2 |
| `M_e4` | 0.974 | 0.956 | 0 | 7 |

The marginal donor-level model remains primary. The sensitivity results are not
used to replace or augment its DEG list.

## Commands executed

```bash
Rscript tests/test_phase08_broad_deg.R

Rscript scripts/08_build_broad_pseudobulk.R \
  --config config/phase08_broad_deg.yml \
  --profile local_pilot \
  --preflight

Rscript scripts/08_build_broad_pseudobulk.R \
  --config config/phase08_broad_deg.yml \
  --profile local_pilot

Rscript scripts/08_run_broad_pseudobulk_de.R \
  --config config/phase08_broad_deg.yml \
  --profile local_pilot

Rscript scripts/08_run_broad_deg_composition_sensitivity.R \
  --config config/phase08_broad_deg.yml \
  --profile local_pilot

Rscript scripts/08_finalize_broad_deg.R \
  --config config/phase08_broad_deg.yml \
  --profile local_pilot

Rscript scripts/08_validate_broad_deg.R \
  --config config/phase08_broad_deg.yml \
  --profile local_pilot \
  --require-status validated_complete

Rscript tests/test_phase08_broad_deg.R \
  --validate-output results/local_pilot/08_deg_broad
```

All script parse checks, the LSF `bash -n` check, synthetic tests, output tests,
and 30 final scientific checks passed.

## Output locations

The pilot wrote only under:

```text
results/local_pilot/08_deg_broad/
```

Key outputs are:

- `broad_deg_results.tsv.gz`: complete annotated tested-gene results;
- `05_by_contrast/*.broad_deg.tsv.gz`: six physical category result files;
- `broad_deg_strict_signatures.tsv.gz`;
- `broad_deg_relaxed_signatures.tsv.gz`;
- `broad_deg_exploratory_signatures.tsv.gz`;
- `broad_core_mito_kda_query_handoff.tsv.gz`;
- `04_sensitivity/broad_deg_composition_adjusted.tsv.gz`;
- `04_sensitivity/broad_deg_sensitivity_summary.tsv`;
- `broad_deg_contrast_status.tsv`;
- `broad_deg_checks.tsv`;
- `broad_deg_artifacts.tsv`; and
- `broad_deg_status.tsv`.

The final artifact manifest contains 38 checksum-recorded files. Existing
`08_mast/`, Phase 12, Phase 18, and Phase 20 artifacts were not modified.

## Production readiness

The local pilot validates the common code path for one broad cell and six
groups. It does not establish that all 42 Minerva contrasts are estimable.

Before Minerva submission:

1. synchronize the new config, mapping, scripts, test, and documentation;
2. confirm all nine Phase 07 pseudobulk bundles and Phase 09 annotation master
   exist under `results/minerva_production/`;
3. run the `minerva_production` preflight;
4. create `results/minerva_production/08_deg_broad/logs/`; and
5. submit `scripts/08_broad_deg_minerva.lsf`.

No Phase 05 normalized RDS or original Phase 08 MAST rerun is needed when the
nine validated Phase 07 count bundles are present.
