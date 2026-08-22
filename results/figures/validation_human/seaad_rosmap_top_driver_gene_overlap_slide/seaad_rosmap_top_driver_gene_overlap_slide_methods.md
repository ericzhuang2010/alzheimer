# ROSMAP–SEA-AD top-driver gene overlap slide: methods

The renderer reads validated VH09 ROSMAP selected units and the independently frozen VH10C SEA-AD top lists, using compact VH10D overlap artifacts as cross-checks. Upstream statuses, checks, registered full-file SHA-256 values, blind-freeze flag, `phase18_parity_query`, and `phase18_parity_query__min3_all` are required. Symbols are split by exact driver class and deduplicated across broad networks. MT geometry is nested because the SEA-AD set is contained in the ROSMAP set; non-MT geometry is disjoint because the intersection is empty. ROSMAP uses an orange hatched outline, SEA-AD uses a teal solid fill, and every region is directly labeled. The visible footer states that network identity is collapsed and distinguishes the two gene-level-only common symbols. The 12 × 5.3 inch asset uses at least 16-point text and is exported as searchable SVG, vector PDF, and 5400 × 2385 PNG at 450 DPI.

## Reproduction command

```bash
python scripts/figures/validation_human/plot_seaad_rosmap_overlap_slide_figures.py \
  --figure gene \
  --output-base results/figures/validation_human \
  --visual-review-status pending
```
