# Phase 12 Minerva KDA results sanity check

## Audit scope

This report records the post-run audit of the Phase 12 production KDA bundle
under:

```text
results/minerva_production/12_kda/
```

The audit was performed on 2026-07-28. It checked the complete output bundle,
result arithmetic, signature and background membership, artifact hashes, and
directed network reachability for representative key drivers.

## Conclusion

The Minerva Phase 12 KDA results look technically correct. The audit found no
discrepancy requiring a rerun.

The production bundle contains exactly nine files, uses the corrected fKDA
implementation, and reports:

- 1,782 planned analyses;
- 1,021 eligible analyses;
- 840 analyses with significant drivers;
- 10,172 key-driver rows;
- zero failed analyses or validation checks;
- 54 fine cell types and nine networks;
- a runtime of 1,553 seconds;
- peak memory use of 3.39 GiB; and
- terminal status `validated_complete`.

The authoritative status and check tables are:

```text
results/minerva_production/12_kda/kda_status.tsv
results/minerva_production/12_kda/kda_checks.tsv
```

## Full-table checks

The following conditions were checked across all 10,172 reported key-driver
rows:

- Every `overlap_count` was positive, with a range of 1–21.
- Every adjusted P value was at most 0.05.
- The number of genes in `Overlap.Items` exactly equaled `overlap_count`.
- Every overlap gene belonged to that run's effective mitochondrial
  signature.
- Every key driver belonged to that run's exact induced-network background.
- `signature_size` equaled the run's effective query size.
- `neighborhood_size + non_neighborhood_size` equaled the effective
  background size.
- All fold-enrichment values were reproduced exactly.
- All corrected hypergeometric log P values were reproduced, with a maximum
  numerical difference below `6 × 10^-14`.
- All 38 recorded artifact hashes matched the current files.
- All compressed files passed gzip integrity checks.

The production bundle also uses the corrected fKDA source checksum:

```text
fed8f89f35a3f08f38a420eb9b26c590cdc5f13a12064af1b9fa4a4cb1168550
```

This is the version in which a zero signature overlap correctly receives an
upper-tail hypergeometric P value of 1. Details of that correction are in
`docs/analysis/kda/fkda_zero_overlap_hypergeometric_bug.md`.

## Directed reachability sanity checks

The run-specific induced network was independently reconstructed for seven
reported drivers: one from every broad network that produced KDA results.
These examples deliberately use drivers that were not themselves members of
the corresponding signature, so every reported overlap required a genuine
outgoing directed path rather than self-coverage at distance zero.

For every example:

- the reconstructed neighborhood size equaled the reported
  `neighborhood_size`;
- the reconstructed covered signature genes exactly equaled
  `Overlap.Items`;
- the reconstructed overlap count equaled `overlap_count`; and
- every shortest directed path was no longer than `BestLayer`.

| Network | Driver | Maximum layer | Neighborhood | Covered signature |
|---|---|---:|---:|---:|
| Astrocytes | `APOE` | 1 | 9 genes | 3/59 |
| Excitatory neurons | `MT-ND4L` | 2 | 8 genes | 3/11 |
| Inhibitory neurons | `MT-CO2` | 3 | 18 genes | 6/6 |
| Microglia | `RPL11` | 3 | 57 genes | 5/17 |
| OPCs | `BEX3` | 1 | 13 genes | 4/79 |
| Oligodendrocytes | `MT-CO2` | 2 | 10 genes | 2/18 |
| Vasculature | `HSPA1A` | 3 | 40 genes | 2/4 |

### Astrocytes: `APOE`

Run:

```text
primary_Ast_GRM3_F_e2_AD_up_mito
```

The layer-one neighborhood contained nine genes and covered three of the 59
effective signature genes:

```text
APOE -> LDHB
APOE -> TUFM
APOE -> CHCHD10
```

The reconstructed covered set was exactly `LDHB`, `TUFM`, and `CHCHD10`.

### Excitatory neurons: `MT-ND4L`

Run:

```text
primary_Exc_L5_ET_F_e33_AD_up_mito
```

The layer-two neighborhood contained eight genes and covered three of 11
effective signature genes:

```text
MT-ND4L -> MT-ND5
MT-ND4L -> MT-ND3
MT-ND4L -> MT-ND5 -> MT-ND1
```

### Inhibitory neurons: `MT-CO2`

Run:

```text
primary_Inh_L3_5_SST_MAFB_F_e4_AD_up_mito
```

The layer-three neighborhood contained 18 genes and covered all six effective
signature genes:

```text
MT-CO2 -> MT-CO3
MT-CO2 -> MT-CYB
MT-CO2 -> MT-CO3 -> MT-ND1
MT-CO2 -> MT-CYB -> MT-ND5
MT-CO2 -> MT-CO3 -> MT-ATP6
MT-CO2 -> MT-CYB -> MT-ND5 -> MT-ND4L
```

### Microglia: `RPL11`

Run:

```text
primary_Mic_P2RY12_M_e4_AD_down_mito
```

The layer-three neighborhood contained 57 genes and covered five of 17
effective signature genes:

```text
RPL11 -> RPS15 -> TMSB10 -> FTH1
RPL11 -> RPS23 -> APOO
RPL11 -> RPS23 -> TXNRD1
RPL11 -> RPS6 -> ATP5F1E
RPL11 -> RPS15 -> UQCRB
```

### OPCs: `BEX3`

Run:

```text
secondary_OPC_male_pool_AD_down_mito
```

The layer-one neighborhood contained 13 genes and covered four of 79
effective signature genes through direct edges:

```text
BEX3 -> HINT1
BEX3 -> CHCHD2
BEX3 -> COX4I1
BEX3 -> UQCRFS1
```

### Oligodendrocytes: `MT-CO2`

Run:

```text
secondary_Oli_female_pool_AD_both_mito
```

The layer-two neighborhood contained ten genes and covered two of 18
effective signature genes:

```text
MT-CO2 -> MT-ND4 -> MT-ND2
MT-CO2 -> MT-CYB -> MT-ND3
```

### Vasculature: `HSPA1A`

Run:

```text
secondary_End_female_pool_AD_down_mito
```

The layer-three neighborhood contained 40 genes and covered two of four
effective signature genes:

```text
HSPA1A -> HSP90AA1 -> PTGES3 -> MRPS6
HSPA1A -> HSPH1 -> HSPD1
```

## Eligibility observations

The complete manifest contains 761 planned rows that were correctly skipped:

- 734 rows had fewer than three effective mitochondrial query genes; and
- 27 rows depended on a source contrast that was not validated.

CAMs and T cells produced no eligible KDA runs. For CAMs, 24 rows were below
the query-size threshold and nine involved an unvalidated source contrast.
All 33 T-cell rows were below the query-size threshold. These are explicit
eligibility outcomes, not computational failures.

Results were produced for the other seven networks:

- Astrocytes;
- Excitatory neurons;
- Inhibitory neurons;
- Microglia;
- OPCs;
- Oligodendrocytes; and
- Vasculature cells.

## Interpretation caveats

### Driver self-membership

Of the 10,172 result rows, 5,349, or approximately 52.6%, have a key driver
that is itself a member of the effective signature. The fKDA neighborhood
includes the starting driver, so such a result receives one self-overlap at
distance zero.

This is expected under the current method and is not a validation error. It
does matter when interpreting a result as a strictly upstream regulator. The
seven reachability examples above deliberately excluded self-member drivers
and still reproduced the reported coverage exactly.

If the scientific objective is specifically to identify non-signature
upstream regulators, that should be evaluated through a separately specified
sensitivity analysis. Rows should not simply be removed after the current BH
correction if new adjusted P values are required.

### Recurrent mitochondrial drivers

The most recurrent reported drivers include mitochondrial genes such as
`MT-CO2`, `MT-CYB`, `MT-ND5`, and `MT-CO3`. This pattern is compatible with
the current candidate and signature definitions, especially because
signature genes are allowed to be tested as drivers. Recurrence alone should
not be interpreted as experimental proof of causality.

### Network interpretation

The checked paths follow the direction of the supplied Bayesian-network
edges. The edges do not encode whether the effect is activating or
inhibitory, and KDA enrichment does not by itself establish biological
causality.

## Primary files for review

```text
results/minerva_production/12_kda/kda_status.tsv
results/minerva_production/12_kda/kda_checks.tsv
results/minerva_production/12_kda/kda_run_manifest.tsv
results/minerva_production/12_kda/kda_results.tsv.gz
results/minerva_production/12_kda/kda_key_driver_summary.tsv
results/minerva_production/12_kda/kda_signature_members.tsv.gz
results/minerva_production/12_kda/kda_background_members.tsv.gz
```
