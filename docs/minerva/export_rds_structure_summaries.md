# Export RDS structure summaries on Minerva

Use `scripts/16_export_rds_structure_summaries.R` to inspect all nine Seurat RDS
files and create one compact JSON data file. Bring that JSON file back to the
local project so the nine Markdown summaries can be generated without copying
the large RDS files.

## Resource requirement

Run this on a Minerva compute node, not a login node. The largest object,
`Excitatory_neurons_set2.rds`, may require approximately 128 GiB of RAM. A
192-GiB compute-node allocation is recommended.

The script reads only one RDS at a time and writes a checkpoint after every
completed object. If the process is interrupted, run the same command again; it
will skip unchanged objects that were already completed.

## 1. Enter the project environment

From the Minerva copy of this repository, use the established environment setup:

```bash
cd /sc/arion/work/zhuane01/alzheimer
source docs/minerva/cmd_to_run_after_logging_in.txt
```

Do this inside an allocated compute-node shell.

## 2. Run the exporter

```bash
Rscript scripts/export_rds_structure_summaries.R \
  --manifest config/minerva_rds_manifest.tsv \
  --input-root /sc/arion/projects/zhangb03a/shared/ROSMAP/Synapse/snRNAseq_MIT/GeneExpression/10x/processed \
  --output results/minerva_production/rds_structure_summaries.json
```

The command processes these manifest IDs:

1. `astrocytes`
2. `excitatory_set1`
3. `excitatory_set2`
4. `excitatory_set3`
5. `immune`
6. `inhibitory`
7. `opcs`
8. `oligodendrocytes`
9. `vasculature`

Do not add `--hash` for the normal export. Hashing would reread roughly 35 GiB of
large files and is unnecessary for preparing the Markdown summaries.

## 3. Check completion

The final terminal message should be:

```text
Status: complete; complete=9; failed=0; missing=0
```

You can also check the JSON without loading any RDS files:

```bash
Rscript -e '
x <- jsonlite::fromJSON(
  "results/minerva_production/rds_structure_summaries.json",
  simplifyVector = FALSE
)
cat("status:", x$run$status, "\n")
cat("complete:", x$run$completed_rds, "\n")
cat("failed:", x$run$failed_rds, "\n")
cat("objects:", paste(names(x$objects), collapse = ", "), "\n")
'
```

Expected values are `status: complete`, `complete: 9`, and `failed: 0`.

## 4. Resume after interruption

Run the same exporter command again. The existing JSON is the checkpoint. An
unchanged object with `status: complete` will be skipped automatically.

Use `--force` only if you intentionally want to discard the checkpoint and
reinspect every RDS from the beginning.

## 5. Bring back this one file

Copy this file from Minerva:

```text
/sc/arion/work/zhuane01/alzheimer/results/minerva_production/rds_structure_summaries.json
```

Place it at the same project-relative location locally:

```text
results/minerva_production/rds_structure_summaries.json
```

The JSON contains only structural summaries, counts, labels, dimensions, and
provenance. It does not contain the expression matrices or individual-level
clinical data.

## Optional single-object test

To inspect just one manifest object, use `--rds-id`. For example:

```bash
Rscript scripts/export_rds_structure_summaries.R \
  --manifest config/minerva_rds_manifest.tsv \
  --input-root /sc/arion/projects/zhangb03a/shared/ROSMAP/Synapse/snRNAseq_MIT/GeneExpression/10x/processed \
  --rds-id vasculature \
  --output results/minerva_production/vasculature_structure_test.json \
  --force
```
