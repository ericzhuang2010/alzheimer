# VH09 and VH10 Execution Summary

VH09 and VH10 completed locally. Every phase reports `validated_complete`, and no optional sensitivity analysis was executed.

## Main results

| Result | Count |
|---|---:|
| Frozen ROSMAP Phase 18 top-five candidate units | 47 |
| Active SEA-AD KDA queries | 42 |
| Calls with at least one significant KDA candidate | 29 |
| Calls with no significant KDA candidate | 13 |
| SEA-AD passing and selected candidate units | 13 |
| SEA-AD unique selected genes | 11 |
| ROSMAP selected units testable in SEA-AD | 36 of 47 |
| Strictly rediscovered ROSMAP units | 6 |

The strict rediscoveries, matched by broad network, gene, and driver class, were:

- Excitatory neurons: `MT-CO2`, `MT-CYB`
- Inhibitory neurons: `MT-CO2`, `MT-CO3`, `MT-CYB`, `MT-ND5`

SEA-AD additionally selected `MT-ND4`, `MT-ATP6`, `HGSNAT`, `BEX3`, `RPS27A`, `RPL30`, and `KANSL1L`. A top-five list was not forced when a KDA call had fewer than five significant candidates.

## MT versus non-MT rediscovery

Yes: under the prespecified strict overlap rule, **no non-MT ROSMAP top-five gene was rediscovered** in SEA-AD.

| Driver class | ROSMAP selected units | Testable in SEA-AD | SEA-AD selected units | Strict rediscoveries |
|---|---:|---:|---:|---:|
| MT | 26 | 19 | 8 | 6 |
| Non-MT | 21 | 17 | 5 | 0 |
| Total | 47 | 36 | 13 | 6 |

This does not mean that SEA-AD produced no non-MT key drivers. SEA-AD selected five non-MT units:

| Broad network | SEA-AD rank | Gene |
|---|---:|---|
| Excitatory neurons | 1 | `HGSNAT` |
| Inhibitory neurons | 1 | `BEX3` |
| Inhibitory neurons | 2 | `RPS27A` |
| Inhibitory neurons | 3 | `RPL30` |
| Oligodendrocytes | 1 | `KANSL1L` |

None of these five matched a ROSMAP Phase 18 non-MT top-five gene in the same broad network. Among the 21 ROSMAP non-MT units, 17 were testable in SEA-AD and all 17 had status `tested_not_selected`; the remaining four were `not_testable`. The gene-only overlap also contained only the same six MT genes, so relaxing the broad-network match would not create a non-MT rediscovery.

The appropriate interpretation is therefore: **non-MT candidates were detected in SEA-AD, but the ROSMAP non-MT top-five selections did not replicate under the current SEA-AD queries, donor support, significance threshold, and top-five selection rule.** This result does not rule out weaker or context-specific non-MT network effects.

## Key outputs

- VH09 status: `results/validation_human/09_rosmap_kda_candidates/status.tsv`
- VH10 status: `results/validation_human/10_seaad_kda_rediscovery/status.tsv`
- SEA-AD selected top lists: `results/validation_human/10_seaad_kda_rediscovery/selected_top_lists.tsv`
- Strict ROSMAP overlap: `results/validation_human/10_seaad_kda_rediscovery/overlap/rosmap_selected_assessment.tsv`
- Summary metrics: `results/validation_human/10_seaad_kda_rediscovery/summary/summary_metrics.tsv`

## Verification

- The Phase 18 replay exactly reproduced 78 passing and 47 selected ROSMAP candidate units across 161 runs, including their ranks.
- Input and output artifact hashes were recorded.
- All six VH09/VH10 unit and integration tests passed.
- No newly generated file exceeds 100 MB; the largest is approximately 2 MB.
- VH09 and VH10 use separate validation directories and did not overwrite existing ROSMAP or earlier SEA-AD results.
- The changes have not been committed to Git.
