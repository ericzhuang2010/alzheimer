# VH12 SEA-AD-Specific Network Rerun Summary

The Phase 12 rerun completed successfully using the SEA-AD-specific Bayesian networks.

## Outputs

- Results: `results/validation_human/12_sex_apoe_kda`
- Analysis status: `results/validation_human/12_sex_apoe_kda/simple_status.tsv`
- Results README: `results/validation_human/12_sex_apoe_kda/README.md`
- Figures: `results/figures/validation_human/phase_12_sex_apoe_simple_aggr_network`
- KDA configuration: `config/phase12_seaad_network_kda.yml`

## Key results

| Metric | Previous network | SEA-AD network |
|---|---:|---:|
| Active KDA calls | 42 | 34 |
| Significant calls | 27 | 29 |
| No-significant-result calls | 15 | 5 |
| Significant returned rows | 201 | 221 |
| Non-mitochondrial retained rows | 121 | 135 |
| Unique non-mitochondrial genes | 91 | 94 |
| Recurrent genes | 20 | 25 |
| Categories with returned genes | 4 | 5 |

## Figures

Both figure bundles were regenerated as 300-DPI PNG, SVG, and PDF files:

- Driver recurrence: `results/figures/validation_human/phase_12_sex_apoe_simple_aggr_network/driver_recurrence`
- Top-five candidates: `results/figures/validation_human/phase_12_sex_apoe_simple_aggr_network/top5_candidates`

The figures use colorblind-safe colors and grayscale-readable hatching.

## Validation and scope

- All 113 validation checks passed.
- All 48 registered artifacts matched their recorded sizes and SHA-256 hashes.
- Previous Phase 11 results were not modified.
- No PowerPoint slides were created or changed.
- The returned-only ACAT aggregation remains exploratory and is not formally FDR-controlled.
- The Vasculature network retains its `encode_only_exploratory` designation.
