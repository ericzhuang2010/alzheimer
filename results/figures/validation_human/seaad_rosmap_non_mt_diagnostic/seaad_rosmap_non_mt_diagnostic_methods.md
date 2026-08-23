# ROSMAP–SEA-AD non-MT diagnostic: methods

The renderer reads archived Phase 18 selection, VH09 frozen ROSMAP units, and VH10A/VH10B/VH10D SEA-AD artifacts. It requires current `validated_complete` statuses, zero failed checks, registered artifact hashes where manifests are available, and frozen full-file SHA-256 values for every input. It also requires the `fdr_only_query_sensitivity` / `posthoc_exploratory__fdr_only__donor3__query3__coverage80__q05` SEA-AD contract. The diagnostic does not read VH05 or VH06.

ROSMAP non-MT units are exact `broad_network + gene` rows from the VH09 selected table. SEA-AD assessability and final-selection status come from the VH10D unit trace. A qualifying SEA-AD run-level return follows the frozen Phase 18 conservative-support gate: adjusted within-run q ≤ 0.05, overlap ≥ 2 query genes, and fold enrichment > 1 in the matching broad network. Phase 18 conservative-support rows provide ROSMAP support strata. The SEA-AD result is explicitly post-hoc exploratory: FDR < 0.05 with no fold-change cutoff, at least three donors in each disease arm, effective query size ≥ 3, aggregate coverage ≥ 0.80, aggregate BH q ≤ 0.05, and at least one qualifying supporting run. ROSMAP retains its frozen Phase 18 selection rules.

The donor context is derived from the current SEA-AD run manifest. F_e2 and M_e2 are wholly source-not-estimable under the donor-3 rule. M_e4 is kept separate: 77 completed contrasts contribute 154 signed directions, all 154 terminate as query-empty, and no M_e4 KDA call is included. Nineteen of 21 units have ROSMAP support in F_e2 or M_e2, three exclusively; 20/21 have support in the broader F_e2/M_e2/M_e4 set. The reverse lookup uses the reclassified Phase 18 call-return audit for two-class aggregate q values and support counts. The figure is titleless for slide composition, uses a 12 × 5.3 inch canvas with at least 16-point text, and exports searchable SVG, vector PDF, and a 5400 × 2385 PNG at 450 DPI.

## Reproduction command

```bash
python scripts/figures/validation_human/plot_seaad_rosmap_non_mt_diagnostic.py \
  --output-root results/figures/validation_human/seaad_rosmap_non_mt_diagnostic \
  --visual-review-status pending
```
