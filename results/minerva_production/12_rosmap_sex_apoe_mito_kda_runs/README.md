# Phase 12 ROSMAP sex/APOE mitochondrial KDA runs

## Status

**Frozen upstream authority.** Phase 12 is deprecated only as a standalone
reporting endpoint. Current sex/APOE-by-broad-cell reporting uses the Phase 20
combined aggregation in:

```text
results/minerva_production/20_sex_apoe_kda_combo/
```

The Phase 12 results are not obsolete. They contain the validated run-level KDA
evidence from which later analyses were derived.

This directory is the KDA execution layer: fine-cell mitochondrial query sets
were tested against their corresponding broad-cell Bayesian networks. Phase 20
combo does not rerun KDA; it filters and aggregates these run-level results.
The former directory name `12_kda` was replaced by the descriptive name
`12_rosmap_sex_apoe_mito_kda_runs`.

Frozen historical figure manifests may still record the former path as the
execution-time location; active code, configuration, and documentation use the
new path.

## Preservation requirement

Keep this directory at its current path and do not modify, rename, or delete
its canonical files. Downstream workflows use fixed paths, schemas, and
SHA-256 identities. The machine-readable status must remain
`validated_complete`.

The original execution configuration is preserved byte-for-byte at:

```text
phase12_kda_execution_config_snapshot.yml
```

`config/phase12_kda.yml` retains the same scientific parameters but now names
this descriptive output directory.

## Downstream dependencies

Direct consumers include:

- Phase 20 combined returned-only aggregation;
- the Phase 11 fine-cell DEG pathway analysis, which uses the exact KDA
  backgrounds;
- current presentation-generation scripts; and
- historical Phase 12, Phase 18, and ROSMAP/SEA-AD validation figures.

The Phase 11 broad-cell pathway analysis depends indirectly on this bundle
through the Phase 11 fine-cell results. Phase 21/22 harmonized broad KDA and
some human-validation workflows use the frozen Phase 12 configuration and
network contract rather than these result tables directly.

## Canonical files

- `kda_run_manifest.tsv`: one row per planned KDA call.
- `kda_signature_members.tsv.gz`: candidate and effective query membership.
- `kda_background_members.tsv.gz`: exact run-specific network backgrounds.
- `kda_results.tsv.gz`: significant within-call KDA returns.
- `kda_key_driver_summary.tsv`: broad-network/driver recurrence summary.
- `kda_qc_summary.tsv`: run-level QC summaries.
- `kda_checks.tsv`: validation checks.
- `kda_artifacts.tsv`: input/output provenance and hashes.
- `kda_status.tsv`: production status.
- `phase12_kda_execution_config_snapshot.yml`: hash-identical configuration
  used for the original production run.

Uncompressed `kda_results.tsv` and `kda_signature_members.tsv` files are
convenience copies; the compressed files above are the canonical registered
artifacts.

## Interpretation

Use Phase 12 when exact fine-cell calls, query membership, network backgrounds,
or within-call KDA results are required. Use Phase 20 combo for the current
aggregated sex/APOE-by-broad-cell driver lists. Neither analysis by itself
establishes causality or a formal difference between sex/APOE groups.
