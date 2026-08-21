# ROSMAP–SEA-AD top-driver gene Venn figure: methods

The renderer reads the validated VH09 ROSMAP Phase 18 selected units and independently frozen VH10C SEA-AD top lists, then uses compact VH10D overlap tables only as cross-checks. It requires `validated_complete` upstream statuses, zero failed upstream checks, registered full-file SHA-256 values, `rosmap_candidate_files_read = False`, and the exact `phase18_parity_query` / `phase18_parity_query__min3_all` SEA-AD selection contract. It does not read the full candidate universes or recompute selection.

Top-display rows are split by exact `case_id` and gene symbols are deduplicated across broad networks. Circle area follows `radius = 0.43 × sqrt(unique genes)` with the same scale in both panels. Because SEA-AD MT is a strict subset of ROSMAP MT, those circles are nested. Because the non-MT intersection is empty, those circles are disjoint. Every gene is printed alphabetically within its region; no P value is calculated for this descriptive view. Fill, outline style, hatch, direct labels, and counts provide redundant encoding. SVG and PDF are vector exports, and SVG text remains searchable. The PNG is 5400 × 3240 at 450 DPI.

## Reproduction command

```bash
python scripts/figures/validation_human/plot_seaad_rosmap_top_driver_gene_venn.py \
  --output-root results/figures/validation_human/seaad_rosmap_top_driver_gene_venn \
  --visual-review-status pending
```
