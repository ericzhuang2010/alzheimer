# SEA-AD KDA call outcomes: methods

The renderer reads the active DEG and VH10 configurations plus the validated VH10B status and compact registered run-QC table and the validated VH10C status, selection checks, and selection freeze. It validates full-file SHA-256 values for consumed compact inputs only; bulky call-return and candidate-test tables are not required because they are not plotted. Status and freeze config hashes must match the active VH10 configuration, and the freeze digest must match VH10C status. The active post-hoc exploratory tier is `posthoc_exploratory__fdr_only__donor3__query3__coverage80__q05`. Queries use `fdr_only_query_sensitivity` (`FDR < 0.05`), at least 3 donors per disease arm upstream, and at least 3 effective query genes per KDA call. The inherited 1.3-fold rule is not an active KDA query gate. The retained selection gates are conservative support ≥1, coverage ≥0.80, and network-BH aggregate q ≤0.05; the per-network/class display limit is 5.

Each `significant_key_drivers > 0` flag must agree with its terminal status. Network-by-direction counts are reconstructed from individual calls and checked across all 14 configured cells, including network/direction combinations with no call. The five equal-size sequence boxes are not area-scaled because units change from calls to return rows to aggregate candidate units. The aggregation ribbon preserves the executed order: `run BH → support ≥1 → coverage ≥0.80 → ACAT → network BH q≤0.05 → class rank`. The SEA-AD selection freeze must state `rosmap_candidate_files_read=False`; ROSMAP remains a frozen external comparison and its candidate identities or thresholds are not used to select SEA-AD units.

The asset is titleless at slide level, uses a 12.0 × 5.3 inch canvas, and keeps all visible text at 16 pt or larger. SVG/PDF retain vector geometry and searchable text; PNG is 5,400 × 2,385 pixels at 450 DPI. Direction is encoded by triangle orientation, and call status is encoded by fill plus direct labels, so the figure remains interpretable in grayscale.

## Reproduction command

```bash
python scripts/figures/validation_human/plot_seaad_kda_call_outcomes.py \
  --output-root results/figures/validation_human/seaad_kda_call_outcomes \
  --visual-review-status pending
```
