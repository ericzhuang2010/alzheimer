# Strict ROSMAP–SEA-AD overlap and paired ranks: methods

The renderer reads validated VH09 ROSMAP selected units, the independently frozen VH10C SEA-AD list, and the VH10D strict overlap and summary tables. Upstream statuses, checks, registered full-file SHA-256 values, blind-freeze flag, `fdr_only_query_sensitivity`, and `posthoc_exploratory__fdr_only__donor3__query3__coverage80__q05` are required before rendering. The SEA-AD tier is explicitly post-hoc exploratory: FDR < 0.05 with no fold-change cutoff, at least three donors in each disease arm, effective query size ≥ 3, aggregate coverage ≥ 0.80, aggregate BH q ≤ 0.05, and at least one qualifying supporting run. The frozen ROSMAP Phase 18 selection is not reclassified under SEA-AD thresholds. ROSMAP scorecard denominators include only selected units in the common assessable universe. A strict shared unit must match broad network, current gene symbol, and exact driver class. The slopegraphs retain the complete MT selected-list union for Excitatory and Inhibitory neurons; unmatched cohort endpoints are drawn in gray and strict matches use navy connectors. Jaccard indices and nominal per-list hypergeometric p values are read from VH10D rather than recomputed. The 12 × 5.3 inch asset uses at least 16-point text and is exported as searchable SVG, vector PDF, and 5400 × 2385 PNG at 450 DPI.

## Reproduction command

```bash
python scripts/figures/validation_human/plot_seaad_rosmap_overlap_slide_figures.py \
  --figure strict \
  --output-base results/figures/validation_human \
  --visual-review-status pending
```
