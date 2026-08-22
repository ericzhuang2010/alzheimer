# SEA-AD fine-supertype DEG landscape: methods

The renderer reads the validated VH08 status, checks, fine contrast status, fine direction handoff, and DEG summary. It requires exact registered full-file SHA-256 values, `validated_complete` status, no failed VH08 check, 774 unique fine-supertype contrasts, and 1,548 unique signed direction slots. The heatmap uses the `fine_supertype_phase18_parity` tier only. A completed cell is the sum of its Dementia-up and Dementia-down parity-qualified feature hits; direction-level counts are independently required to reconstruct the contrast-level total. Not-estimable cells remain distinct from completed zero-hit cells. Rows follow the fixed seven-network order, then descending total parity hits and stable `supertype_id` within network. Bars use `log10(1 + count)` length while printing untransformed counts. The figure does not use broad pooled or broad stratified DEG tiers.

The asset is titleless at slide level, uses a 12.0 × 5.3 inch canvas, and keeps all visible text at 16 pt or larger. SVG/PDF retain vector geometry and searchable text; PNG is 5,400 × 2,385 pixels at 450 DPI. Color is backed by direct labels and distinct white/gray states.

## Reproduction command

```bash
python scripts/figures/validation_human/plot_seaad_fine_deg_landscape.py \
  --output-root results/figures/validation_human/seaad_fine_deg_landscape \
  --visual-review-status pending
```
