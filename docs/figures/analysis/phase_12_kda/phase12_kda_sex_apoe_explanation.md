# Phase 12 KDA Panel B: Sex/APOE-Stratified Evidence

This figure maps where prioritized genes show network-based support as potential “key drivers” of Alzheimer’s-associated mitochondrial expression signatures.

## How to read it

- **Rows:** gene–cell-network pairs. A gene can recur because its evidence is evaluated separately in different networks.
- **Left panel:** enrichment for mitochondrial genes **upregulated in AD**.
- **Right panel:** enrichment for mitochondrial genes **downregulated in AD**.
- **Columns:** female and male APOE strata: ε2, ε3/3, and ε4.
- **Dot size:** fraction of tested KDA runs significant after within-run BH correction.
- **Dot color:** mean \(-\log_{10}\) raw KDA P value; darker blue means stronger average evidence. Values are visually capped at about 5.
- **Small outlined circle:** the gene was tested, but no run was significant.
- **Gray ×:** no eligible/tested run—not evidence of absence.
- **Right bar:** overall MeanOfLog ranking score, normalized within that cell network. The adjacent fraction is ranking coverage, not significant runs—for example, `133/133` means the gene could be ranked in all 133 eligible directional runs.
- **Colored strips:** identify cell networks only; their colors do not encode evidence.

For example, excitatory-neuron **RPL11** in male ε2 AD-down has 8 significant runs out of 14, with mean \(-\log_{10}P=6.08\). It therefore appears as a large, dark-blue circle. By contrast, OPC **RPS15** in the same stratum is extremely dark and full-sized but represents only 1/1 run; it is strong within that run but has far less replication.

## Main patterns

The clearest broad pattern is **male ε2 support for the AD-down mitochondrial signature**. It appears across several networks:

- Excitatory RPL11: 8/14 significant runs
- Inhibitory RPS15: 9/10
- Inhibitory LAMTOR5: 5/9
- Astrocytic APOE: 2/3
- Excitatory TMEM147: 4/10
- OPC RPS15, FTL, and ANKRD11: each 1/1
- Oligodendrocyte RPL11: 1/1

A complementary pattern occurs for the **female ε2 AD-up signature**, especially in astrocytes and excitatory neurons:

- Excitatory RPL11: 6/12
- Excitatory TMEM147: 6/11
- Excitatory SELENOW: 5/12
- Astrocytic RPL11, APOE, and RPS15: each 1/3

Other more localized signals include:

- **Female ε3/3 AD-up:** strong OPC RPS15, FTL, and ANKRD11 signals, but each is based on only one run.
- **Female ε4 AD-down:** RPL11, TMEM147, and SELENOW in excitatory neurons, plus BEX3, LAMTOR5, and RPS15 in inhibitory neurons.
- **Male ε4:** microglial SLC11A1 for AD-up and microglial RPL11/RPS15 plus astrocytic APOE/RPL11 for AD-down.

Overall, 45 of the 192 displayed cells contain at least one significant run, 128 were tested without a significant run, and 19 lacked an eligible/tested run.

## Important interpretation limits

This is a **prioritized, descriptive evidence map**, not a comprehensive screen:

- Rows were preselected using a conservative screen for nuclear, query-independent candidates, with at least one robust result and adequate ranking coverage.
- At most three genes per network are shown; no vasculature candidate passed the same display criteria.
- The dots summarize KDA analyses, not donors or independent experimental replications.
- AD-up and AD-down describe the mitochondrial gene set—not whether the proposed driver activates or represses it.
- MeanOfLog is a ranking statistic, not a formally combined P value.
- Visual differences between sex/APOE columns are not formal interaction tests.
- KDA detects enrichment of a candidate’s downstream network neighborhood; it suggests regulatory relevance but does not establish causality.

The most defensible conclusion is therefore: **male ε2 AD-down and female ε2 AD-up are the broadest recurring patterns, with additional APOE- and cell-network-specific signals that should be treated as hypotheses for donor-aware interaction testing and experimental validation.**

The exact values are available in the [plotted-data table](../../../../results/figures/analysis/phase12_kda/phase12_kda_sex_apoe_plotted_data.tsv), with the full definitions in the [figure design document](phase_12_kda_sex_apoe_dot_heatmap_design.md).
