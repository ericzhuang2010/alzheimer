# ATP synthase genes in `LAMTOR5` KDA neighborhoods

**Analysis date:** 2026-08-02  
**Source:** `results/minerva_production/12_kda/kda_results.tsv`  
**Scope:** all 96 significant `LAMTOR5` KDA calls; fewer than 1,000 words

## Main result

Yes. Four structural ATP synthase genes occur in `LAMTOR5` neighborhood
overlaps in addition to the regulator `ATP5IF1`:

- `ATP5MC2`: membrane c-ring subunit
- `ATP5PF`: peripheral-stalk F6 subunit
- `ATP5PD`: peripheral-stalk d subunit
- `ATP5MG`: membrane g subunit

At least one of these four structural genes occurs in **77/96 `LAMTOR5`
calls** (30/38 primary and 47/58 secondary). Sixty-one calls contain both
`ATP5IF1` and a structural subunit, 16 contain a structural subunit without
`ATP5IF1`, 9 contain `ATP5IF1` without another subunit, and 10 contain neither.
No other `ATP5*` gene, `MT-ATP6`, or `MT-ATP8` appears in the `LAMTOR5`
overlap lists.

One call means one significant candidate × KDA-run row. U/D/B means AD-up,
AD-down, or the derived `AD_both_mito` union. Secondary pools and B calls
reuse primary data and are not independent replications.

## Call summary

| Gene | Role | Calls P/S/total | U/D/B | Excitatory / inhibitory | Fine types | Global | Strict primary directional |
|---|---|---:|---:|---:|---:|---:|---:|
| `ATP5IF1` | ATP synthase inhibitor; comparator | 28/42/70 | 12/26/32 | 59/11 | 11 | 5 | 15 |
| `ATP5MC2` | Membrane c-ring | 23/33/56 | 11/20/25 | 56/0 | 7 | 4 | 12 |
| `ATP5PF` | Peripheral stalk F6 | 7/10/17 | 0/10/7 | 0/17 | 3 | 1 | 4 |
| `ATP5PD` | Peripheral stalk d | 2/8/10 | 0/5/5 | 0/10 | 3 | 1 | 1 |
| `ATP5MG` | Membrane g | 4/5/9 | 0/5/4 | 0/9 | 3 | 2 | 2 |

The main pattern is branch-specific:

- `ATP5MC2` is the dominant structural partner and is exclusively
  excitatory.
- `ATP5PF`, `ATP5PD`, and `ATP5MG` are exclusively inhibitory and occur only
  in AD-down or derived-union calls.
- `ATP5IF1` spans both neuronal networks.

## Sex–APOE distribution

Counts include directional and B calls. Groups with zero calls for all five
genes are omitted: primary female ε3/ε3, male ε3/ε3, and male ε4, plus the
secondary ε3/ε3 pool.

| Tier and group | `ATP5IF1` | `ATP5MC2` | `ATP5PF` | `ATP5PD` | `ATP5MG` |
|---|---:|---:|---:|---:|---:|
| Primary female ε2 | 8 | 8 | 0 | 0 | 0 |
| Primary female ε4 | 6 | 5 | 2 | 0 | 0 |
| Primary male ε2 | 14 | 10 | 5 | 2 | 4 |
| Secondary female pool | 10 | 9 | 2 | 0 | 0 |
| Secondary male pool | 8 | 8 | 1 | 3 | 1 |
| Secondary ε2 pool | 19 | 13 | 5 | 3 | 4 |
| Secondary ε4 pool | 5 | 3 | 2 | 2 | 0 |

The primary structural-subunit evidence is concentrated in female ε2,
female ε4, and male ε2. Male ε2 is the only primary group containing all four
structural genes.

## Fine-cell distribution of structural subunits

Values are primary/secondary/total. Cell types with no structural subunit are
omitted.

| Fine cell type | `ATP5MC2` | `ATP5PF` | `ATP5PD` | `ATP5MG` |
|---|---:|---:|---:|---:|
| `Exc L2-3 CBLN2 LINC02306` | 3/0/3 | 0/0/0 | 0/0/0 | 0/0/0 |
| `Exc L3-4 RORB CUX2` | 4/5/9 | 0/0/0 | 0/0/0 | 0/0/0 |
| `Exc L3-5 RORB PLCH1` | 4/6/10 | 0/0/0 | 0/0/0 | 0/0/0 |
| `Exc L4-5 RORB GABRG1` | 2/4/6 | 0/0/0 | 0/0/0 | 0/0/0 |
| `Exc L4-5 RORB IL1RAPL2` | 6/10/16 | 0/0/0 | 0/0/0 | 0/0/0 |
| `Exc L5-6 RORB LINC02196` | 2/4/6 | 0/0/0 | 0/0/0 | 0/0/0 |
| `Exc L6 THEMIS NFIA` | 2/4/6 | 0/0/0 | 0/0/0 | 0/0/0 |
| `Inh ALCAM TRPM3` | 0/0/0 | 0/0/0 | 0/0/0 | 0/1/1 |
| `Inh CUX2 MSR1` | 0/0/0 | 2/2/4 | 1/1/2 | 2/2/4 |
| `Inh L3-5 SST MAFB` | 0/0/0 | 2/2/4 | 0/0/0 | 2/2/4 |
| `Inh LAMP5 NRG1 (Rosehip)` | 0/0/0 | 3/6/9 | 1/4/5 | 0/0/0 |
| `Inh PVALB HTR4` | 0/0/0 | 0/0/0 | 0/3/3 | 0/0/0 |

## Network paths and interpretation

| Gene | Shortest directed path in the supporting network |
|---|---|
| `ATP5IF1` | Excitatory: `LAMTOR5 → ATP5IF1`; inhibitory: `LAMTOR5 → ATP5PF → ATP5IF1` |
| `ATP5MC2` | Excitatory: `LAMTOR5 → POP7 → ATP5MC2` |
| `ATP5PF` | Inhibitory: `LAMTOR5 → ATP5PF` |
| `ATP5PD` | Inhibitory: `LAMTOR5 → ATP5PF → NDUFA12 → ATP5PD` |
| `ATP5MG` | Inhibitory: `LAMTOR5 → ATP5PF → NDUFA12 → ATP5MG` |

The result is broader than a `LAMTOR5`–`ATP5IF1` pair. It supports a candidate
link from nutrient sensing to several parts of ATP synthase: inhibitory control,
the proton-conducting c-ring, the peripheral stalk, and membrane organization.
The excitatory and inhibitory branches use different subunits, which argues
for cell-class-specific validation rather than one pooled neuronal model.

KDA supplies directed topology but not edge sign or causality. The strongest
manuscript wording is: **“LAMTOR5 neighborhoods repeatedly contained ATP
synthase regulatory and structural genes, with `ATP5MC2` dominant in
excitatory neurons and `ATP5PF`/`ATP5PD`/`ATP5MG` confined to inhibitory
neurons.”**

