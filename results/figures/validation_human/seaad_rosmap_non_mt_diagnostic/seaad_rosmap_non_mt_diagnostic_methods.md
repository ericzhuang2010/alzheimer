# ROSMAP–SEA-AD non-MT diagnostic: methods

The renderer reads validated Phase 12 KDA, archived Phase 18 selection, VH09 frozen ROSMAP units, and VH10A/VH10B/VH10D SEA-AD artifacts. It requires current `validated_complete` statuses, zero failed checks, registered artifact hashes where manifests are available, and frozen full-file SHA-256 values for every input. The diagnostic does not read VH05 or VH06.

ROSMAP non-MT units are exact `broad_network + gene` rows from the VH09 selected table. SEA-AD assessability and final-selection status come from the VH10D unit trace. A qualifying SEA-AD run-level return follows the frozen Phase 18 conservative-support gate: adjusted within-run q ≤ 0.05, overlap ≥ 2 query genes, and fold enrichment > 1 in the matching broad network. Phase 18 conservative-support rows provide ROSMAP support strata. The 20/21 context count means at least one conservative ROSMAP supporting run occurred in F_e2, M_e2, or M_e4; it does not require exclusive support in those strata. SEA-AD marks those three strata structurally unestimable because one disease arm contains fewer than five independent donors.

The reverse lookup uses the reclassified Phase 18 call-return audit for two-class aggregate q values. KANSL1L, absent from that explicit audit, is recovered from the registered Phase 18 gene-case summary. Phase 12 primary results verify the two Inhibitory RPL30 size-3 returns and the absence of an Oligodendrocyte KANSL1L primary return. The figure is titleless for slide composition, uses a 12 × 5.3 inch canvas with at least 16-point text, and exports searchable SVG, vector PDF, and a 5400 × 2385 PNG at 450 DPI.

## Reproduction command

```bash
python scripts/figures/validation_human/plot_seaad_rosmap_non_mt_diagnostic.py \
  --output-root results/figures/validation_human/seaad_rosmap_non_mt_diagnostic \
  --visual-review-status pending
```
