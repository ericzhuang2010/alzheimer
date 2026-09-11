# Harmonized broad-cell KDA effective-query-size sensitivity

**Assessment date:** 2026-09-11  
**ROSMAP KDA source:** Phase 22  
**SEA-AD KDA source:** VH14

## Question

This sensitivity analysis evaluates minimum effective query sizes of **3
(current), 5, 10, 20, and 30 genes** for the harmonized broad-cell KDA.

The threshold refers to the number of effective query genes remaining after
network mapping. The donor minimum is held at the current **3 donors per
disease arm** in both cohorts so that this test changes only the query-size
gate.

## Method and interpretation boundary

This is an exact threshold-gating sensitivity, not a statistical hypothesis
test. For each proposed threshold, an existing KDA call and its significant
returns are retained only when the recorded effective query size is at least
the threshold.

No DEG model was refitted and KDA was not rerun. Raising the query-size gate
does not change the query, network, or statistics for a retained call; it only
removes calls below the new threshold.

One merged up/down query is used per broad-cell x sex/APOE contrast. Therefore,
the number of query-passing contrasts and the number of KDA runs are identical
in this analysis.

## Results

| Cohort | Minimum effective query genes | Source-estimable contrasts | Query-passing contrasts | KDA runs | Significant KD rows | Unique non-`MT-*` KDs |
|---|---:|---:|---:|---:|---:|---:|
| ROSMAP | 3 | 42 | 3 | 3 | 39 | 33 |
| ROSMAP | 5 | 42 | 2 | 2 | 30 | 24 |
| ROSMAP | 10 | 42 | 1 | 1 | 26 | 20 |
| ROSMAP | 20 | 42 | 1 | 1 | 26 | 20 |
| ROSMAP | 30 | 42 | 1 | 1 | 26 | 20 |
| SEA-AD | 3 | 28 | 5 | 5 | 24 | 18 |
| SEA-AD | 5 | 28 | 5 | 5 | 24 | 18 |
| SEA-AD | 10 | 28 | 3 | 3 | 8 | 3 |
| SEA-AD | 20 | 28 | 3 | 3 | 8 | 3 |
| SEA-AD | 30 | 28 | 2 | 2 | 7 | 3 |

“Significant KD rows” includes the raw significant returns from the retained
KDA calls. “Unique non-`MT-*` KDs” excludes `MT-*` genes and deduplicates gene
symbols within each cohort; this is the biologically relevant driver count.

The source-estimable contrast counts remain 42 for ROSMAP and 28 for SEA-AD at
every query threshold because the query-size gate is applied downstream of
contrast estimation.

## Cohort-specific effects

### ROSMAP

The three current executed query sizes are **3, 8, and 78 genes**.

- A minimum of 5 removes `OPCs x F_e4`, eliminating 9 driver rows.
- A minimum of 10 additionally removes `Astrocytes x F_e4`, eliminating 4
  more driver rows.
- Thresholds of 20 and 30 make no further change.
- At thresholds of 10 or higher, only the low-support
  `Vasculature x M_e2` call remains. This call has a 78-gene effective query
  and returns 26 significant rows, representing 20 unique non-`MT-*` drivers.

Consequently, increasing the query-size floor to 10 or higher makes the
ROSMAP result **more dominated by the low-donor 4-versus-3 vasculature call**,
not less dominated by it.

### SEA-AD

The five current executed query sizes are **5, 9, 21, 43, and 45 genes**.

- A minimum of 5 changes nothing.
- A minimum of 10 removes `Microglia x M_e33` and
  `Astrocytes x F_e4`. Significant driver rows fall from 24 to 8, and unique
  non-`MT-*` drivers fall from 18 to 3.
- A minimum of 20 makes no further change.
- A minimum of 30 additionally removes `Oligodendrocytes x M_e33`. Its sole
  returned row is an `MT-*` gene, so the unique non-`MT-*` driver count remains
  3.

## Cross-cohort validation

- Cross-cohort non-`MT-*` driver overlap remains **zero at every tested query
  threshold**.
- At thresholds 3 and 5, `Astrocytes x F_e4` remains the only exact stratum
  executed in both cohorts, and it has no shared drivers.
- At thresholds 10, 20, and 30, there is **no exact stratum executed in both
  cohorts**. Cross-cohort validation is therefore unavailable rather than
  negative at these thresholds.

## Conclusion

Among the stricter alternatives, **5 effective query genes is the least
disruptive sensitivity reference**. It removes the smallest ROSMAP query while
preserving all SEA-AD KDA runs and the only matched cross-cohort stratum.

Thresholds of 10 or higher substantially reduce cross-cohort assessability and
leave ROSMAP dominated by the low-support `Vasculature x M_e2` result. None of
the tested thresholds produces non-`MT-*` cross-cohort driver validation.

The 5-gene result should be interpreted as a sensitivity reference, not as a
new confirmatory KDA rule.

## Source artifacts

- ROSMAP run manifest:
  `results/minerva_production/22_harmonized_broad_kda_combo/run_manifest.tsv`
- ROSMAP significant returns:
  `results/minerva_production/22_harmonized_broad_kda_combo/significant_returns.tsv`
- SEA-AD run manifest:
  `results/validation_human/14_harmonized_broad_kda_combo/run_manifest.tsv`
- SEA-AD significant returns:
  `results/validation_human/14_harmonized_broad_kda_combo/significant_returns.tsv`
- Presentation audit table:
  `results/presentations/09162026_query_size_sensitivity/sensitivity_summary.tsv`
