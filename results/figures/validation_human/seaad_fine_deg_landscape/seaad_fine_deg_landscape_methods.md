# SEA-AD fine-supertype DEG landscape: methods

The renderer reads the validated VH08 status and compact registered checks, fine contrast status, direction handoff, query index, and DEG summary together with the active DEG and VH10 configurations. It validates only consumed compact files against the VH08 artifact manifest; absent bulky DEG shards, filters, and diagnostics are not figure inputs. Status/config and VH10-authority hashes must agree. The active post-hoc exploratory query is `fdr_only_query_sensitivity` (`FDR < 0.05`), with at least 3 donors per disease arm and at least 20 nuclei per profile. The inherited `phase18_parity_query` rule (`FDR < 0.05 AND abs(logFC) > log2(1.3)`) is auxiliary context only. The heatmap uses the `fine_supertype_phase18_parity` tier and posthoc_exploratory__fdr_only__donor3__query3__coverage80__q05 protocol identity. Each completed cell is the sum of its Dementia-up and Dementia-down FDR-only feature hits; direction-level counts must independently reconstruct the contrast total. Not-estimable cells remain distinct from completed zero-hit cells. Rows follow the configured network order, then descending active hits and stable `supertype_id`. Bars use `log10(1 + count)` length while printing untransformed counts. Broad pooled/stratified tiers and ROSMAP candidate identities are not used.

The asset is titleless at slide level, uses a 12.0 × 5.3 inch canvas, and keeps all visible text at 16 pt or larger. SVG/PDF retain vector geometry and searchable text; PNG is 5,400 × 2,385 pixels at 450 DPI. Color is backed by direct labels and distinct white/gray states.

## Reproduction command

```bash
python scripts/figures/validation_human/plot_seaad_fine_deg_landscape.py \
  --output-root results/figures/validation_human/seaad_fine_deg_landscape \
  --visual-review-status pending
```
