# Phase 18 non-MT Driver Sex/APOE Figure — Historical Rendering

> The former Case 3 is now called `non_mt_driver`. This explanation describes
> the historical rendering; quantitative annotations should be regenerated
> from the current two-class Phase 18 table.

This figure shows where the Case 3 key-driver evidence occurs across sex,
APOE group, AD direction, and broad cell-type network. It is a validated
descriptive figure—44/44 checks passed—but it does not test sex-by-APOE
interactions.

## How to read the rows

Each row is a gene–broad-network context, not just a gene. A gene therefore
appears multiple times when it passes in multiple networks. There are 22 rows
for 15 genes.

Left-side annotations:

- **Net.**: colored strip identifying the broad network.
- **Circle**: solid dot means the context appeared in the Case 3 circle; an
  open dot means it passed but was below that network's five-gene display cap.
- **Extended**: diamond means membership in the broader mitochondrial
  reference. NCOA1 is the only marked gene.

For example, RPS15 has three rows. Its excitatory-neuron row has an open
circle because it passed all gates but ranked 20th and was not displayed in
the top-five circle.

## Heatmap columns

The first six columns are AD-up mitochondrial queries; the next six are
AD-down queries. Within each direction, the order is:

| Sex | APOE strata |
|---|---|
| Female | ε2, ε3/ε3, ε4 |
| Male | ε2, ε3/ε3, ε4 |

These correspond to the project source groups `F_e2`, `F_e33`, `F_e4`,
`M_e2`, `M_e33`, and `M_e4`.

Each cell combines eligible fine-cell-type queries for that gene, stratum,
direction, and fixed broad Bayesian network.

## Meaning of the heatmap symbols

| Symbol | Meaning |
|---|---|
| Filled circle | At least one usable query passed every conservative-support gate |
| Small open circle | Tested, but no query passed every conservative-support gate |
| Gray X | Eligible queries existed, but none produced a usable test |
| Dash | No eligible query existed |

For filled circles:

- **Dot area** is the fraction of usable fine-cell-type queries that
  conservatively support the driver.
- **Dot color** is capped `−log10(stratum ACAT P)`.
- Larger dots mean greater recurrence within that stratum.
- More yellow dots mean smaller descriptive ACAT P values.

A large dot does not necessarily represent broad evidence. For example,
`1/1` produces the maximum dot size but represents only one usable query. The
counts on the right are needed to distinguish high fractions from broad
recurrence.

An open circle does not necessarily mean ACAT P = 1. It means that no
individual query met every conservative-support gate.

## Right-side annotations

These summarize the entire gene–network row across all 12 strata.

1. **Network aggregate q**  
   Neutral point on a separate `−log10(q)` scale. Farther right means a
   smaller, stronger network-level aggregate q value. This is the official
   Phase 18 selection evidence.

2. **Support / usable**  
   Exact number of conservatively supporting queries divided by usable
   queries.

3. **Coverage**  
   Usable queries divided by eligible queries. This measures completeness,
   not significance.

4. **Tier**

   - Blue: Tier 1, recurrent/stable
   - Orange: Tier 2, localized or less stable
   - Gray: stability not assessable

5. **Rank**  
   The candidate's rank among Case 3 candidates within that broad network.
   Smaller is better. This is network-specific, not a global gene rank.

## Representative examples

- **RPL11—excitatory neurons:** Tier 1, rank 1, complete coverage (`97/97`)
  and support in `20/97` queries. Supporting strata include AD-up female ε2
  (`5/12`) and AD-down male ε2 (`8/13`), among others.

- **RPS15—inhibitory neurons:** Tier 1, rank 1, `11/28` supporting queries
  with full coverage. Evidence is concentrated particularly in AD-down male
  ε2 (`7/8`).

- **RPS15—OPCs:** Extremely strong aggregate q, rank 1, but only `2/6`
  supporting queries. The two large yellow dots each represent `1/1`,
  illustrating why dot size must be interpreted with the total counts.

- **APOE—astrocytes:** Tier 1, rank 4, with `4/21` supporting queries. Support
  occurs in AD-up female ε2 and AD-down male ε2 and ε4 strata.

- **NCOA1—OPCs:** Marked as an extended mitochondrial-reference gene. It has
  localized support (`1/6`), specifically AD-down female ε4 (`1/1`), and its
  stability tier is not assessable.

## Overall descriptive pattern

Across all 22 rows, support appears most frequently in:

- AD-down male ε2: 62 supporting runs in 19 gene-network rows
- AD-up female ε2: 28 supporting runs in 11 rows
- AD-down female ε4: 16 supporting runs in 10 rows
- AD-down male ε4: 10 supporting runs in 7 rows

This concentration is descriptive. The strata have different eligible and
usable denominators, reuse broad Bayesian networks, and are not independent
external replications. Therefore, the figure supports hypotheses about
sex/APOE-patterned evidence but does not establish sex or APOE specificity.

The supporting caption and data are available in
[case3_sex_apoe](../../../../results/figures/analysis/phase_18_key_driver_selection/case3_sex_apoe/).
