# Phase 18 three-case circular figures: methods

## Inputs and selection

The renderer required the validated Phase 18 production bundle at `results/minerva_production/18_key_driver_selection/`. Display membership and rank were read from `key_driver_top5.tsv`; the renderer did not recalculate ACAT, multiple-testing correction, candidate status, or rank.

Within each broad network and case, the frozen Phase 18 rank is ascending aggregate ACAT q value, ascending aggregate ACAT P value for q-value ties, and current gene symbol as the deterministic final tie-breaker. Up to five passing candidates were displayed without backfilling.

## Geometry and encoding

All three circles used the same seven-network order and 35-slot geometry (five display slots per network). Candidate bar height was `min(-log10(q), 15) / 15`, with one common scale across cases. Network identity was encoded by the colorblind-aware outer band and by text labels. Repeated displayed symbols within one case were connected from their strongest uncapped evidence sector to each other occurrence. The legend occupied a dedicated panel to the right of the circular plot; the plot center contained neither legend content nor an opaque mask, leaving cross-network link curves visible end to end. All legend text was rendered at twice its original size and arranged in a compact key. Broad-network labels were enlarged and positioned close to the outer band.

## Export

Figures were rendered with base R and Cairo on a 12 × 7.2 inch canvas. SVG and PDF are the authoritative vector files; PNG review copies were exported at 450 dpi.

## Reproduction command

```bash
Rscript --vanilla \
  scripts/figures/analysis/phase_18_key_driver_selection/ \
  visualize_phase18_three_case_circular.R \
  --input-dir results/minerva_production/18_key_driver_selection \
  --output-dir results/figures/analysis/phase_18_key_driver_selection/three_case_circular \
  --top-per-network 5 \
  --evidence-cap 15 \
  --png-dpi 450
```
