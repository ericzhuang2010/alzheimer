# VH09 and amended VH10 execution summary

The post-hoc exploratory SEA-AD rerun completed locally on 2026-08-22
(America/New_York; UTC completion 2026-08-23). VH07, VH08, and every VH10
subphase report `validated_complete`. The canonical SEA-AD results were
overwritten; the frozen ROSMAP VH09 reference was not changed.

## Executed threshold tier

- Donor support: at least 3 donors per disease arm
- Active query: signed core-MitoCarta genes with within-contrast FDR `< 0.05`
- Candidate coverage: at least 0.50
- Aggregate ACAT BH q: at most 0.10
- Result tier:
  `posthoc_exploratory__fdr_only__donor3__query3__coverage50__q10`

## Main results

| Result | Count |
|---|---:|
| Fine contrasts meeting donor support | 382 |
| Completed fine contrasts | 381 |
| Completed signed source directions | 762 |
| Active SEA-AD KDA queries | 42 |
| Calls with at least one significant KDA return | 27 |
| Calls with no significant KDA return | 15 |
| SEA-AD passing and selected candidate units | 14 |
| SEA-AD unique selected genes | 12 |
| ROSMAP selected units testable in SEA-AD | 36 of 47 |
| Strictly rediscovered ROSMAP units | 6 |

The strict rediscoveries, matched by broad network, gene, and driver class,
remain:

- Excitatory neurons: `MT-CO2`, `MT-CYB`
- Inhibitory neurons: `MT-CO2`, `MT-CO3`, `MT-CYB`, `MT-ND5`

SEA-AD selected eight additional strict units: `MT-ND4`, `MT-ATP6`,
`HGSNAT`, `MT-ND1`, `BEX3`, `RPS27A`, `RPL30`, and `KANSL1L`.
`MT-ND1` is the additional selected gene relative to the superseded
13-unit SEA-AD result.

## Selected candidates

| Broad network | Driver class | SEA-AD rank | Gene | Aggregate q |
|---|---|---:|---|---:|
| Excitatory neurons | MT | 1 | `MT-CO2` | 1.19e-21 |
| Excitatory neurons | MT | 2 | `MT-CYB` | 5.72e-05 |
| Excitatory neurons | MT | 3 | `MT-ND4` | 0.0309 |
| Excitatory neurons | MT | 4 | `MT-ATP6` | 0.0309 |
| Excitatory neurons | non-MT | 1 | `HGSNAT` | 0.0218 |
| Inhibitory neurons | MT | 1 | `MT-CO2` | 1.80e-11 |
| Inhibitory neurons | MT | 2 | `MT-ND5` | 3.92e-06 |
| Inhibitory neurons | MT | 3 | `MT-CO3` | 7.67e-05 |
| Inhibitory neurons | MT | 4 | `MT-CYB` | 8.05e-05 |
| Inhibitory neurons | MT | 5 | `MT-ND1` | 0.0971 |
| Inhibitory neurons | non-MT | 1 | `BEX3` | 0.00656 |
| Inhibitory neurons | non-MT | 2 | `RPS27A` | 0.00931 |
| Inhibitory neurons | non-MT | 3 | `RPL30` | 0.0953 |
| Oligodendrocytes | non-MT | 1 | `KANSL1L` | 0.0902 |

All selected units have coverage 1.0. Three depend on the amended q<=0.10
gate: `MT-ND1`, `RPL30`, and `KANSL1L`. A top-five list was not forced
when fewer than five candidates passed.

## MT versus non-MT rediscovery

| Driver class | ROSMAP selected units | Testable in SEA-AD | SEA-AD selected units | Strict rediscoveries |
|---|---:|---:|---:|---:|
| MT | 26 | 19 | 9 | 6 |
| Non-MT | 21 | 17 | 5 | 0 |
| Total | 47 | 36 | 14 | 6 |

No non-MT ROSMAP top-five unit was rediscovered under the strict
network-gene-class rule. This does not mean SEA-AD produced no non-MT key
drivers: it selected `HGSNAT`, `BEX3`, `RPS27A`, `RPL30`, and
`KANSL1L`, but none matched a frozen ROSMAP non-MT top-five gene in the same
broad network.

## Key outputs

- VH08 status:
  `results/validation_human/08_deg/status.tsv`
- VH10 status:
  `results/validation_human/10_seaad_kda_rediscovery/status.tsv`
- SEA-AD selected lists:
  `results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/seaad_top5.tsv`
- Strict overlap:
  `results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_candidate_overlap.tsv`
- Summary by network/class:
  `results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_overlap_summary.tsv`

## Verification

- VH07 reproduced 382 donor-supported and 381 model-feasible fine contrasts.
- VH08 completed all 381 model-feasible fine contrasts and published 762
  query-ready directions.
- VH10A derived 42 active calls from the amended artifacts; this count was not
  hard-coded from the superseded run.
- VH10C independently recomputed 14 passing units using coverage>=0.50,
  aggregate q<=0.10, and at least one conservative supporting run.
- VH10D replayed all 161 frozen ROSMAP runs and exactly reproduced the frozen
  78 passing and 47 selected units and their ranks.
- ROSMAP result files were read-only and unchanged.
