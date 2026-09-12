# Tutorial: understanding Section 3, “OXPHOS and the respiratory chain form the shared pathway/network core”

**Source section:** [Joint Phase 11–12 synthesis](phase11_phase12_joint_mitochondrial_discussion.md)  
**Audience:** readers with a high-school-level biology background  
**Purpose:** explain the discovery, conclusion, evidence, prior work, and limitations in Section 3 without making the result sound more causal than it is

## 1. The central idea

Phase 11 and Phase 12 used different methods, but both repeatedly pointed to
the mitochondrial respiratory chain. Phase 11 found respiratory-chain genes
concentrated among the strongest differences between sex/APOE groups. Phase 12
found the same kinds of genes inside many candidate-driver network
neighborhoods. This agreement makes the respiratory chain a strong **shared
readout of AD-associated mitochondrial change**. It does not automatically
make every respiratory-chain gene a cause of AD or a useful drug target.

## 2. Vocabulary

| Term | Meaning |
|---|---|
| **Respiratory chain** | Protein complexes in the inner mitochondrial membrane that transfer electrons and help create the proton gradient used to make ATP. |
| **OXPHOS** | Oxidative phosphorylation: respiratory complexes I–IV build the gradient, and Complex V uses it to produce ATP. |
| **Complex I, III, IV, V** | Major OXPHOS machines. Complex II is also part of respiration, but it was not the dominant repeated signal described here. |
| **mtDNA gene** | A gene encoded by mitochondrial DNA. Names often begin with `MT-`, such as `MT-CO2`. |
| **Nuclear gene** | A gene stored in the cell nucleus. Most mitochondrial proteins are encoded this way and later imported into mitochondria. |
| **Low tail** | The 200 genes with the most negative similarity scores in a Phase 11 comparison. Here, “low” means the two compared profiles tend to disagree in direction. |
| **Fold enrichment** | How much more common a gene set is than expected. A value of 2.5 means about 2.5 times the expected concentration. |
| **BH FDR** | A multiple-testing-adjusted statistical value. Smaller values provide stronger evidence that an enrichment is not a chance result under the analysis model. |
| **KDA call** | A Phase 12 key-driver-analysis result linking one candidate to a network neighborhood for one query and context. It is not a causal experiment. |
| **Topology** | The pattern of connections in a network. |
| **Sentinel** | A reliable indicator that a system is changing, even if it is not the upstream cause of that change. |

## 3. The title, phrase by phrase

> **“OXPHOS and the respiratory chain form the shared pathway/network core”**

“Shared” means the signal appears in both analytical phases. “Pathway” refers
mainly to the Phase 11 gene-set results. “Network” refers to the Phase 12
neighborhood results. “Core” means respiratory machinery is the most recurrent
common endpoint; it does not mean every cell or stratum changes identically.

> **“[Rediscovery plus new cross-scale topology extension]”**

The rediscovery is that mitochondrial respiration is altered in AD, which has
been reported many times. The extension is the attempt to connect a broad
pathway pattern to fine-cell, sex/APOE-specific network neighborhoods in the
same analytical framework.

## 4. Discovery paragraph, sentence by sentence

> **“Phase 11 and Phase 12 converge on complexes I, III, IV, and V as the
> dominant mitochondrial endpoint: OXPHOS occupies every Phase 11 divergent
> tail, while mtDNA and structural respiratory genes dominate recurrent Phase
> 12 neighborhoods.”**

This sentence contains two observations:

1. In Phase 11, OXPHOS genes repeatedly appeared among the genes that most
   strongly distinguished the compared sex/APOE profiles.
2. In Phase 12, genes encoding physical respiratory-chain parts repeatedly
   occurred as candidates or members of network neighborhoods.

“Converge” is appropriate because two analyses point to the same biological
system. It does not mean the analyses are independent replications: they use
related data and signatures.

## 5. Conclusion paragraph, sentence by sentence

> **“Mitochondrial and OXPHOS dysfunction in AD are established.”**

Earlier RNA, protein, enzyme, and respiration studies already support altered
mitochondrial energy biology in AD. Therefore, the general statement “OXPHOS
is involved in AD” is a rediscovery, not a new claim.

> **“The new contribution is a cell-type- and sex/APOE-resolved chain from
> directional pathway phenotype to candidate network topology.”**

The proposed new contribution has three levels:

1. identify whether a pathway tends to be AD-up or AD-down in a particular
   sex/APOE group;
2. locate that signal in particular fine cell types; and
3. ask which candidate-centered networks contain the same genes.

This is a chain of statistical evidence, not yet a demonstrated molecular
chain of cause and effect.

> **“The joint evidence supports a respiratory sentinel program, not the claim
> that each structural subunit is an upstream therapeutic driver.”**

Respiratory genes may behave like dashboard warning lights: many illuminate
when the energy system is stressed. A warning light is informative, but
replacing the bulb does not repair the engine. Likewise, frequent detection of
`MT-CO2` or `COX4I1` may make it a useful readout without proving that directly
targeting it would correct AD biology.

## 6. Understanding the Phase 11 evidence table

Each row asks whether OXPHOS genes are unusually common among 200 genes in a
low-similarity tail.

| Comparison | Plain-language reading |
|---|---|
| Female versus male, all APOE | 53 of 200 genes are OXPHOS genes, 2.47-fold more than expected; the very small FDR supports a non-random concentration. |
| ε2 versus ε3/ε3 | 53 genes and 2.50-fold enrichment show strong APOE-group divergence. |
| ε4 versus ε3/ε3 | 48 genes and 2.23-fold enrichment show a similar, slightly smaller concentration. |
| Female versus male within ε2 | 56 genes and 2.66-fold enrichment are the strongest count and enrichment in the table. |
| Female versus male within ε3/ε3 | 49 genes and 2.33-fold enrichment show the pattern is not limited to ε2. |
| Female versus male within ε4 | 47 genes and 2.13-fold enrichment show it also persists within ε4. |

The FDR values—from `1.99 × 10^-8` to `1.18 × 10^-16`—are all very small.
That supports enrichment under the statistical model, but it does not measure
biological effect size or causality.

Thirty-five OXPHOS genes occur in all six low tails. Complex IV is especially
consistent: 11 or 12 of its 12 measured genes appear in every comparison.
This recurrence is why the section calls respiration the shared core.

## 7. Understanding the Phase 12 counts

- `MT-CO2`: 550 KDA rows
- `MT-ND4`: 402 rows
- `MT-CO3`: 399 rows
- `MT-CYB`: 397 rows

These are **rows or calls**, not 550 people, experiments, or independent
replications. A gene can recur because related signatures are tested in many
contexts or because it is highly connected.

Two audit numbers explain the caution:

- `3,036 / 10,172 = 29.8%` of all KDA rows use an mtDNA gene as the candidate;
- 5,349 rows contain the candidate in the query set that was used to find it.

Candidate self-membership can make a candidate look more impressive. For
example, `COX4I1` appears in 169 calls but is already a query member in 149.
That does not invalidate all 169 calls; it means only the self-independent
subset provides cleaner driver-nomination evidence.

## 8. How prior work changes the interpretation

[Liang et al. (2008)](https://doi.org/10.1073/pnas.0709259105) reported lower
electron-transport and energy-metabolism transcripts in laser-captured AD
neurons. [Rice et al. (2015)](https://doi.org/10.3233/JAD-142937) found that
whole tissue and isolated neurons could show opposite OXPHOS directions,
illustrating why cell composition matters.

Biochemical and proteomic studies have reported altered respiratory enzymes,
Complex I loss or reduced respiratory capacity, and ATP-synthase oxidation
([Bubber et al., 2005](https://doi.org/10.1002/ana.20474);
[Trumpff et al., 2022](https://doi.org/10.1016/j.heliyon.2022.e09353);
[Troutwine et al., 2022](https://doi.org/10.1016/j.nbd.2022.105781);
[Terni et al., 2010](https://doi.org/10.1111/j.1750-3639.2009.00266.x)).
[Wang et al. (2020)](https://doi.org/10.1186/s13024-020-00384-6) likewise found
a broad mitochondrial protein signature across tissues.

Together, these papers support the biological theme. They do not independently
reproduce the exact Phase 11–12 sex/APOE network topology.

## 9. What could create a misleading recurrence?

- Several mtDNA genes are transcribed together, so their RNA measurements are
  not fully independent.
- More mitochondria per cell can raise many mitochondrial RNAs at once.
- Postmortem RNA quality can affect measured abundance.
- Broad, repeatedly reused networks can generate repeated motifs.
- Highly connected genes have more chances to appear.
- A candidate already present in the query has an automatic advantage.

The decisive reanalysis would keep mtDNA genes in the biological query but
exclude them from candidacy, compare candidates with genes matched for degree,
expression, and mitochondrial annotation, and then measure protein abundance
and respiratory-complex activity.

## 10. One-sentence takeaway

Both phases robustly identify the respiratory chain as a recurring,
context-dependent AD-associated readout, but the present data do not show that
every frequently observed respiratory subunit is an upstream cause or drug
target.
