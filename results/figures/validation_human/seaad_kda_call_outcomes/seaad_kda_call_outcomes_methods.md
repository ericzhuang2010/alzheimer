# SEA-AD KDA call outcomes: methods

The renderer reads the validated VH10B run-QC table and status plus the validated VH10C status and selection checks. It requires exact registered full-file SHA-256 values, 42 unique completed KDA calls, 29 calls with at least one significant return, 13 calls with none, and 208 significant return rows. Each `significant_key_drivers > 0` flag must agree with its terminal status. Network-by-direction counts are reconstructed from individual calls and checked against all 14 cells, including OPC and Vasculature combinations with no included call. The five equal-size sequence boxes are not area-scaled because units change from calls to return rows to aggregate candidate units. The aggregation ribbon preserves the executed order: `run BH → conservative support → coverage ≥0.80 → ACAT → network BH → class rank`.

The asset is titleless at slide level, uses a 12.0 × 5.3 inch canvas, and keeps all visible text at 16 pt or larger. SVG/PDF retain vector geometry and searchable text; PNG is 5,400 × 2,385 pixels at 450 DPI. Direction is encoded by triangle orientation, and call status is encoded by fill plus direct labels, so the figure remains interpretable in grayscale.

## Reproduction command

```bash
python scripts/figures/validation_human/plot_seaad_kda_call_outcomes.py \
  --output-root results/figures/validation_human/seaad_kda_call_outcomes \
  --visual-review-status pending
```
