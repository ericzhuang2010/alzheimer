# Detailed KDA evidence for three Phase 11–12 mitochondrial connections

**Analysis date:** 2026-08-02  
**Scope:** `APOE`–`TUFM`/ATP synthase, `LAMTOR5`–`ATP5IF1`, and
`GABARAPL2`–`CHCHD2`/`PARK7`  
**Main data:** `results/minerva_production/12_kda/kda_results.tsv` and
`kda_run_manifest.tsv`  
**Cross-phase context:** Phase 08 differential-expression outputs and the
[joint Phase 11–12 discussion](phase11_phase12_joint_mitochondrial_discussion.md)

## How to read the counts

- One **KDA call** is one significant candidate-gene × KDA-run row. Significance
  is BH-adjusted within that run (`adjusted_p_value <= 0.05`).
- **Primary** runs use one exact sex–APOE group: female ε2, female ε3/ε3,
  female ε4, male ε2, male ε3/ε3, or male ε4.
- **Secondary** runs pool primary groups by sex or APOE. These pools overlap
  and reuse primary data; they are sensitivity analyses, not independent
  replications.
- `AD_both_mito` is the union of that run's AD-up and AD-down signatures. It
  also reuses the directional genes and is not an independent result.
- A named downstream gene is counted only when it appears in
  `overlap_items`, meaning that it is both in the run's mitochondrial
  signature and in the candidate's best enriched downstream neighborhood.
- In the tables below, **U/D/B (total)** means AD-up / AD-down /
  `AD_both_mito` calls. **P/S/total** means primary / secondary / all calls.
- The **strict** screen keeps primary directional calls, removes candidate-self
  overlap and mtDNA-only support, requires at least two remaining overlap
  genes, and requires at least ten effective query genes.
- The available-run denominators are 52 primary + 45 secondary astrocyte runs,
  212 + 206 excitatory-neuron runs, and 164 + 203 inhibitory-neuron runs.

KDA identifies enriched directed neighborhoods. It does not show activation or
inhibition, and it does not establish causality. The AD-up or AD-down label
describes the mitochondrial query, not the expression direction of the KDA
candidate.

## Overall evidence

| Candidate and connection | Candidate calls P/S/total | Calls containing named downstream gene(s) P/S/total | Strict candidate / connection calls | Global candidate / connection calls |
|---|---:|---:|---:|---:|
| `APOE` → `TUFM` | 7/13/20 | 7/13/20 | 4 / 4 | 7 / 7 |
| `APOE` → any ATP-synthase subunit | 7/13/20 | 3/10/13 | 4 / 2 | 7 / 3 |
| `LAMTOR5` → `ATP5IF1` | 38/58/96 | 28/42/70 | 20 / 15 | 9 / 5 |
| `GABARAPL2` → `CHCHD2` | 32/47/79 | 25/41/66 | 17 / 15 | 26 / 15 |
| `GABARAPL2` → `PARK7` | 32/47/79 | 16/33/49 | 17 / 9 | 26 / 10 |
| `GABARAPL2` → both `CHCHD2` and `PARK7` | 32/47/79 | 13/29/42 | 17 / 7 | 26 / 5 |

Key points:

- Primary calls are the main evidence. Secondary calls increase recurrence but
  do not add independent samples.
- `TUFM` appears in every `APOE` call. The ATP-synthase component is narrower:
  13 of 20 calls.
- `ATP5IF1` appears in 70 of 96 `LAMTOR5` calls.
- At least one of `CHCHD2` or `PARK7` appears in 73 of 79 `GABARAPL2`
  calls; both appear together in 42.
- All primary calls for `APOE`, `LAMTOR5`, and `GABARAPL2` are
  candidate-self-independent.

## 1. Astrocyte APOE connects to TUFM and ATP synthase

### Direct result

- `APOE` has 20 astrocyte calls: 7 primary and 13 secondary, across all three
  astrocyte fine cell types.
- Recurrence is 20/97 eligible astrocyte runs (20.6%): 7/52 primary (13.5%)
  and 13/45 secondary (28.9%).
- All 20 calls contain `TUFM`: 10 directional and 10 `AD_both_mito` calls.
- `ATP5PB` occurs in 13 calls (3 primary, 10 secondary).
- `ATP5F1A` occurs in 6 calls (2 primary, 4 secondary), all of which also
  contain `ATP5PB`.
- No AD-up `APOE` call contains an ATP-synthase subunit. The ATP-synthase
  evidence is limited to AD-down and derived-union queries.
- Seven calls are global. Four calls pass the strict screen; all four contain
  `TUFM`, and two contain an ATP-synthase subunit.
- The 20 enriched-neighborhood adjusted P values range from
  5.76 × 10^-5 to 0.0363; median fold enrichment is 17.3. These statistics
  test the complete neighborhood, not the `APOE`–`TUFM` pair alone.

### Fixed-network topology

- Direct astrocyte-network edges: `APOE → TUFM`, `APOE → ATP5PB`,
  `APOE → LDHB`, and `APOE → CHCHD10`.
- A two-edge path connects `APOE` to `ATP5F1A`:
  `APOE → LDHB → ATP5F1A`.
- Two calls selected a one-layer neighborhood and 18 selected a two-layer
  neighborhood. A two-layer best result does not remove the direct edges; it
  means the larger cumulative neighborhood gave the strongest enrichment.

These are directions in the fixed Bayesian network used by KDA. They are not
proof that APOE protein directly regulates these genes or that the effect is
positive.

### Sex–APOE and direction distribution

| Tier | Group | `APOE`/`TUFM` U/D/B (total) | Calls with any ATP5 subunit U/D/B (total) |
|---|---|---:|---:|
| Primary | Female ε2 | 1/0/1 (2) | 0/0/0 (0) |
| Primary | Female ε3/ε3 | 0/0/0 (0) | 0/0/0 (0) |
| Primary | Female ε4 | 0/0/0 (0) | 0/0/0 (0) |
| Primary | Male ε2 | 0/2/1 (3) | 0/2/1 (3) |
| Primary | Male ε3/ε3 | 0/0/0 (0) | 0/0/0 (0) |
| Primary | Male ε4 | 0/1/1 (2) | 0/0/0 (0) |
| Secondary | Female pool | 1/0/1 (2) | 0/0/0 (0) |
| Secondary | Male pool | 0/2/3 (5) | 0/2/2 (4) |
| Secondary | ε2 pool | 0/2/2 (4) | 0/2/2 (4) |
| Secondary | ε3/ε3 pool | 0/0/0 (0) | 0/0/0 (0) |
| Secondary | ε4 pool | 0/1/1 (2) | 0/1/1 (2) |

### Fine-cell distribution

Every `APOE` call contains `TUFM`, so the `APOE` and `APOE`–`TUFM` counts are
identical.

| Astrocyte fine cell type | `APOE`/`TUFM` P/S/total | Any ATP5 subunit P/S/total |
|---|---:|---:|
| `Ast CHI3L1` | 2/3/5 | 0/2/2 |
| `Ast DPP10` | 1/4/5 | 1/4/5 |
| `Ast GRM3` | 4/6/10 | 2/4/6 |

### Cross-phase interpretation

- Phase 08/11 finds 19 `TUFM` DEG occurrences across 16 fine cell types and
  all six strata: 3 AD-up and 16 AD-down.
- The closest cross-phase match is `Ast GRM3`: `TUFM` is AD-up in female ε2
  (log2FC +0.506) and AD-down in male ε2 (log2FC -0.939).
- Matching primary KDA calls place `TUFM` in `APOE` neighborhoods for female
  ε2 AD-up and male ε2 AD-down. This is the clearest exact bridge between the
  Phase 11 direction and Phase 12 topology.
- The female-ε2 `Ast GRM3` AD-up overlap is `LDHB`, `TUFM`, and `CHCHD10`;
  it does not contain an ATP-synthase gene.
- The male-ε2 `Ast GRM3` AD-down overlap contains `ATP5PB`, `LDHB`, `TUFM`,
  `ATP5F1A`, and `AGT`. Male-ε2 `Ast DPP10` AD-down contains `ATP5PB`,
  `LDHB`, `TUFM`, and `AGT`.

### Publishable interpretation

- Strongest statement: **astrocyte APOE is repeatedly nominated above a
  `TUFM`-containing mitochondrial-translation/metabolic signature.**
- More limited statement: **an ATP-synthase component is present mainly in
  male/ε2 and pooled AD-down neighborhoods.** It should not be generalized to
  the female-ε2 AD-up result.
- APOE-dependent astrocyte metabolism and mitochondrial function have prior
  support, while the exact `APOE`–`TUFM` direction remains a new hypothesis
  ([Schmukler et al., 2020](https://doi.org/10.1038/s41419-020-02776-4);
  [Williams et al., 2020](https://doi.org/10.1016/j.nbd.2020.104742)).
- `TUFM` has separate AD-model support, but reverse or feedback effects remain
  possible ([Zhong et al., 2021](https://doi.org/10.1096/fj.202002461R)).

## 2. LAMTOR5 connects nutrient sensing to ATP5IF1

### Direct result

- `LAMTOR5` has 96 calls: 38 primary and 58 secondary, across 15 neuronal fine
  cell types.
- By network, there are 62 excitatory calls (25 primary, 37 secondary) and 34
  inhibitory calls (13 primary, 21 secondary).
- Recurrence is 62/418 eligible excitatory runs (14.8%) and 34/367 eligible
  inhibitory runs (9.3%). Combined recurrence is 96/785 (12.2%).
- `ATP5IF1` occurs in 70 calls: 28 primary and 42 secondary, across 11 fine
  cell types.
- The 70 calls comprise 12 AD-up, 26 AD-down, and 32 `AD_both_mito` calls.
- Only 9 of 96 `LAMTOR5` calls are global; 5 of the 70 `ATP5IF1`-containing
  calls are global. This supports a recurrent local bridge, not a universal
  root driver.
- Twenty `LAMTOR5` calls pass the strict screen; 15 retain `ATP5IF1`.
- For the 70 `ATP5IF1`-containing calls, adjusted P ranges from
  1.03 × 10^-5 to 0.0430 and median fold enrichment is 14.1. These values
  apply to the enriched neighborhood, not the single edge.

### Fixed-network topology

- Excitatory network: direct edge `LAMTOR5 → ATP5IF1`.
- Inhibitory network: two-edge path
  `LAMTOR5 → ATP5PF → ATP5IF1`.
- Among the 70 `ATP5IF1`-containing calls, 29 have best layer 2 and 41 have
  best layer 3. The target can be closer than the selected cumulative layer.

The topology gives a plausible route from Ragulator/lysosomal nutrient sensing
to ATP synthase control. It does not give the sign of that route.

### Sex–APOE and direction distribution

| Tier | Group | All `LAMTOR5` U/D/B (total) | With `ATP5IF1` U/D/B (total) |
|---|---|---:|---:|
| Primary | Female ε2 | 5/0/5 (10) | 4/0/4 (8) |
| Primary | Female ε3/ε3 | 0/1/1 (2) | 0/0/0 (0) |
| Primary | Female ε4 | 0/5/3 (8) | 0/4/2 (6) |
| Primary | Male ε2 | 0/10/8 (18) | 0/7/7 (14) |
| Primary | Male ε3/ε3 | 0/0/0 (0) | 0/0/0 (0) |
| Primary | Male ε4 | 0/0/0 (0) | 0/0/0 (0) |
| Secondary | Female pool | 5/3/5 (13) | 4/2/4 (10) |
| Secondary | Male pool | 0/8/6 (14) | 0/4/4 (8) |
| Secondary | ε2 pool | 4/8/11 (23) | 4/6/9 (19) |
| Secondary | ε3/ε3 pool | 0/1/0 (1) | 0/0/0 (0) |
| Secondary | ε4 pool | 0/4/3 (7) | 0/3/2 (5) |

The primary `LAMTOR5`–`ATP5IF1` signal is therefore restricted to female ε2,
female ε4, and male ε2. The female-ε3/ε3 `LAMTOR5` calls do not contain
`ATP5IF1`, and there are no primary male-ε3/ε3 or male-ε4 calls.

### Fine-cell distribution

| Fine cell type | Network | All `LAMTOR5` P/S/total | With `ATP5IF1` P/S/total |
|---|---|---:|---:|
| `Exc L2-3 CBLN2 LINC02306` | Excitatory | 3/0/3 | 3/0/3 |
| `Exc L3-4 RORB CUX2` | Excitatory | 4/5/9 | 2/4/6 |
| `Exc L3-5 RORB PLCH1` | Excitatory | 4/6/10 | 4/6/10 |
| `Exc L4-5 RORB GABRG1` | Excitatory | 2/4/6 | 2/4/6 |
| `Exc L4-5 RORB IL1RAPL2` | Excitatory | 6/10/16 | 6/10/16 |
| `Exc L5-6 RORB LINC02196` | Excitatory | 2/4/6 | 2/4/6 |
| `Exc L5/6 IT Car3` | Excitatory | 2/4/6 | 2/4/6 |
| `Exc L6 THEMIS NFIA` | Excitatory | 2/4/6 | 2/4/6 |
| `Inh ALCAM TRPM3` | Inhibitory | 0/2/2 | 0/0/0 |
| `Inh CUX2 MSR1` | Inhibitory | 2/2/4 | 2/2/4 |
| `Inh L3-5 SST MAFB` | Inhibitory | 2/2/4 | 2/2/4 |
| `Inh LAMP5 NRG1 (Rosehip)` | Inhibitory | 3/6/9 | 0/0/0 |
| `Inh PVALB CA8 (Chandelier)` | Inhibitory | 2/0/2 | 0/0/0 |
| `Inh PVALB HTR4` | Inhibitory | 2/5/7 | 1/2/3 |
| `Inh VIP CLSTN2` | Inhibitory | 2/4/6 | 0/0/0 |

The connection is broad in excitatory neurons but selective in inhibitory
neurons: only `Inh CUX2 MSR1`, `Inh L3-5 SST MAFB`, and `Inh PVALB HTR4`
contain `ATP5IF1`.

### Cross-phase interpretation

- Phase 08/11 finds 34 `ATP5IF1` DEG occurrences across 20 fine cell types and
  five strata: 8 AD-up and 26 AD-down.
- By stratum, the DEG counts are female ε2 4 up/0 down, female ε3/ε3 0/0,
  female ε4 0/10, male ε2 3/9, male ε3/ε3 0/4, and male ε4 1/3.
- The primary KDA connection matches the strongest Phase 11 directions:
  female-ε2 AD-up, female-ε4 AD-down, and male-ε2 AD-down.
- `ATP5IF1` has no significant KDA candidate calls of its own. In this
  analysis it is supported as a downstream mediator/readout, not as an
  upstream key-driver candidate.

### Publishable interpretation

- Strongest statement: **`LAMTOR5` repeatedly marks neuronal mitochondrial
  neighborhoods containing `ATP5IF1`, with exact support in female ε2,
  female ε4, and male ε2 primary signatures.**
- The direct excitatory edge makes the hypothesis especially testable. The
  inhibitory evidence should be described as a two-step path through
  `ATP5PF`.
- Ragulator–mTORC1 nutrient sensing and neuronal ATP5IF1 biology are supported
  separately, but their AD connection is not yet established
  ([Bar-Peled et al., 2012](https://doi.org/10.1016/j.cell.2012.07.032);
  [Esparza-Moltó et al., 2021](https://doi.org/10.1371/journal.pbio.3001252)).
- A useful perturbation test is paired `LAMTOR5` CRISPRi/CRISPRa followed by
  `ATP5IF1`, lysosomal mTORC1 localization, autophagic flux, ATP-synthase
  activity, respiration, proton leak, and mtROS measurements. Reciprocal
  `ATP5IF1` perturbation is needed to test mediation.

## 3. GABARAPL2 connects autophagic flux to CHCHD2 and PARK7

### Direct result

- `GABARAPL2` has 79 calls: 32 primary and 47 secondary, across 13 neuronal
  fine cell types.
- There are 77 excitatory calls (30 primary, 47 secondary) and only 2
  inhibitory calls (both primary).
- Recurrence is 77/418 eligible excitatory runs (18.4%) but only 2/367
  inhibitory runs (0.5%). This is mainly an excitatory-neuron result.
- `CHCHD2` occurs in 66 calls (25 primary, 41 secondary) across 11 fine cell
  types.
- `PARK7` occurs in 49 calls (16 primary, 33 secondary) across 7 fine cell
  types.
- Both occur together in 42 calls (13 primary, 29 secondary), all in the
  excitatory network. Of the 79 calls, 24 contain `CHCHD2` alone, 7 contain
  `PARK7` alone, 42 contain both, and 6 contain neither.
- The 42 complete-module calls comprise 6 AD-up, 15 AD-down, and 21
  `AD_both_mito` calls.
- Twenty-six `GABARAPL2` calls are global, but only 5 complete-module calls are
  global.
- Seventeen candidate calls pass the strict screen: 15 contain `CHCHD2`, 9
  contain `PARK7`, and 7 contain both.

### Fixed-network topology

- Excitatory network: direct edge `GABARAPL2 → CHCHD2`.
- Excitatory network: three-edge path
  `GABARAPL2 → MAGEF1 → SNAPC5 → PARK7`.
- All 49 `PARK7`-containing calls, and all 42 complete-module calls, select a
  three-layer neighborhood.
- `CHCHD2` is present in 15 layer-2 and 51 layer-3 calls.
- Neither target is present in the two inhibitory `GABARAPL2` calls.

The `CHCHD2` connection is therefore more direct in the fitted network than
the `PARK7` connection. The KDA output supports a shared downstream module; it
does not show direct GABARAPL2–PARK7 binding.

### Sex–APOE and direction distribution

| Tier | Group | All `GABARAPL2` U/D/B (total) | With `CHCHD2` | With `PARK7` | With both |
|---|---|---:|---:|---:|---:|
| Primary | Female ε2 | 3/1/3 (7) | 3/0/2 (5) | 2/0/1 (3) | 2/0/1 (3) |
| Primary | Female ε3/ε3 | 0/0/0 (0) | 0/0/0 (0) | 0/0/0 (0) | 0/0/0 (0) |
| Primary | Female ε4 | 0/3/2 (5) | 0/3/2 (5) | 0/1/1 (2) | 0/1/1 (2) |
| Primary | Male ε2 | 2/6/5 (13) | 1/5/4 (10) | 1/5/5 (11) | 0/4/4 (8) |
| Primary | Male ε3/ε3 | 0/3/3 (6) | 0/2/2 (4) | 0/0/0 (0) | 0/0/0 (0) |
| Primary | Male ε4 | 1/0/0 (1) | 1/0/0 (1) | 0/0/0 (0) | 0/0/0 (0) |
| Secondary | Female pool | 2/2/3 (7) | 2/2/3 (7) | 2/1/3 (6) | 2/1/3 (6) |
| Secondary | Male pool | 2/6/7 (15) | 1/5/5 (11) | 1/5/5 (11) | 0/4/4 (8) |
| Secondary | ε2 pool | 4/6/8 (18) | 4/5/8 (17) | 2/5/7 (14) | 2/4/7 (13) |
| Secondary | ε3/ε3 pool | 0/2/1 (3) | 0/1/1 (2) | 0/0/0 (0) | 0/0/0 (0) |
| Secondary | ε4 pool | 0/2/2 (4) | 0/2/2 (4) | 0/1/1 (2) | 0/1/1 (2) |

The broad `GABARAPL2`–`CHCHD2` result spans more groups than the complete
three-gene module. Primary `PARK7` and complete-module support is concentrated
in female ε2, female ε4, and male ε2.

### Fine-cell distribution

| Fine cell type | Network | All `GABARAPL2` P/S/total | With `CHCHD2` | With `PARK7` | With both |
|---|---|---:|---:|---:|---:|
| `Exc L2-3 CBLN2 LINC02306` | Excitatory | 4/8/12 | 4/8/12 | 4/8/12 | 4/8/12 |
| `Exc L3-4 RORB CUX2` | Excitatory | 2/4/6 | 2/4/6 | 2/4/6 | 2/4/6 |
| `Exc L3-5 RORB PLCH1` | Excitatory | 2/4/6 | 2/4/6 | 2/4/6 | 2/4/6 |
| `Exc L4-5 RORB GABRG1` | Excitatory | 4/5/9 | 2/4/6 | 2/4/6 | 2/4/6 |
| `Exc L4-5 RORB IL1RAPL2` | Excitatory | 4/8/12 | 3/6/9 | 2/5/7 | 1/3/4 |
| `Exc L5/6 IT Car3` | Excitatory | 2/4/6 | 0/2/2 | 2/4/6 | 0/2/2 |
| `Exc L5/6 NP` | Excitatory | 2/2/4 | 2/2/4 | 0/0/0 | 0/0/0 |
| `Exc L6 CT` | Excitatory | 0/1/1 | 0/0/0 | 0/0/0 | 0/0/0 |
| `Exc L6 THEMIS NFIA` | Excitatory | 2/4/6 | 2/4/6 | 2/4/6 | 2/4/6 |
| `Exc L6b` | Excitatory | 1/1/2 | 1/1/2 | 0/0/0 | 0/0/0 |
| `Exc NRGN` | Excitatory | 2/4/6 | 2/4/6 | 0/0/0 | 0/0/0 |
| `Exc RELN CHD7` | Excitatory | 5/2/7 | 5/2/7 | 0/0/0 | 0/0/0 |
| `Inh LAMP5 NRG1 (Rosehip)` | Inhibitory | 2/0/2 | 0/0/0 | 0/0/0 | 0/0/0 |

The complete module is most consistent in superficial/RORB excitatory types
and `Exc L6 THEMIS NFIA`. Several other excitatory types carry `CHCHD2`
without `PARK7`, and the inhibitory result contains neither target.

### Cross-phase interpretation

- Phase 08/11 finds 36 `CHCHD2` DEG occurrences across 23 fine cell types and
  all six strata: 11 AD-up and 25 AD-down.
- `CHCHD2` is mainly female-ε2 AD-up (6/0), female-ε4 AD-down (0/8), and
  male-ε2 AD-down (1/12), matching the main KDA directions.
- Phase 08/11 finds 21 `PARK7` DEG occurrences across 17 fine cell types and
  four strata: 7 AD-up and 14 AD-down. Its strongest directions are female ε2
  (6/0) and male ε2 (1/11), with 0/2 in female ε4 and 0/1 in male ε3/ε3.
- This alignment supports the targets as context-specific mitochondrial
  readouts. It still does not establish that changing `GABARAPL2` changes
  their expression or protein activity.

### Publishable interpretation

- Strongest statement: **`GABARAPL2` is a recurrent excitatory-neuron
  candidate linked directly in the fitted network to `CHCHD2` and more
  distantly to `PARK7`.**
- The broad module is consistent with autophagy/mitophagy and mitochondrial
  stress control. Autophagic flux itself was not measured in these human data.
- GABARAP-family function in autophagosome–lysosome fusion and a
  GABARAPL2-dependent AD-model benefit are already supported
  ([Wang et al., 2015](https://doi.org/10.1073/pnas.1507263112);
  [Dai et al., 2025](https://doi.org/10.1186/s40035-025-00514-4)).
- A reported GABARAP-family interaction with CHCHD2/CHCHD10 supports the
  direct-network component; the `PARK7` connection remains less established
  ([Zhou et al., 2026](https://doi.org/10.1080/15548627.2026.2678427)).
- Perturb `GABARAPL2` abundance and Ser72 state in excitatory neurons, then
  measure autophagosome–lysosome fusion, mitophagy, `CHCHD2`, `PARK7`,
  respiration, and AD-relevant phenotypes. `PARK7` loss can test whether it is
  required for the response.

## Named genes when treated as KDA candidates

Downstream overlap and candidate nomination are different. This table gives
the call count for every named gene when it is itself tested as a KDA
candidate. U/D/B is shown separately for primary and secondary calls.

| Gene as candidate | Calls P/S/total | P U/D/B; S U/D/B | Primary-group distribution | Secondary-pool distribution | Networks; fine types | Self-containing / global |
|---|---:|---|---|---|---|---:|
| `APOE` | 7/13/20 | 1/3/3; 1/5/7 | Fε2=2, Mε2=3, Mε4=2 | female=2, male=5, ε2=4, ε4=2 | Astrocytes=20; 3 | 0 / 7 |
| `TUFM` | 15/24/39 | 0/8/7; 1/13/10 | Fε4=4, Mε2=9, Mε4=2 | female=2, male=10, ε2=10, ε4=2 | Astrocytes=3, excitatory=36; 9 | 39 / 0 |
| `ATP5PB` | 3/2/5 | 1/1/1; 1/0/1 | Fε3/ε3=2, Mε3/ε3=1 | female=2 | Excitatory=5; 2 | 5 / 0 |
| `ATP5F1A` | 0/0/0 | 0/0/0; 0/0/0 | none | none | none; 0 | 0 / 0 |
| `LAMTOR5` | 38/58/96 | 5/16/17; 9/24/25 | Fε2=10, Fε3/ε3=2, Fε4=8, Mε2=18 | female=13, male=14, ε2=23, ε3/ε3=1, ε4=7 | Excitatory=62, inhibitory=34; 15 | 0 / 9 |
| `ATP5IF1` | 0/0/0 | 0/0/0; 0/0/0 | none | none | none; 0 | 0 / 0 |
| `GABARAPL2` | 32/47/79 | 6/13/13; 8/18/21 | Fε2=7, Fε4=5, Mε2=13, Mε3/ε3=6, Mε4=1 | female=7, male=15, ε2=18, ε3/ε3=3, ε4=4 | Excitatory=77, inhibitory=2; 13 | 0 / 26 |
| `CHCHD2` | 35/56/91 | 7/13/15; 13/23/20 | Fε2=10, Fε3/ε3=4, Fε4=8, Mε2=10, Mε3/ε3=3 | female=20, male=9, ε2=14, ε3/ε3=4, ε4=9 | Excitatory=70, inhibitory=18, OPC=3; 17 | 91 / 31 |
| `PARK7` | 3/3/6 | 1/2/0; 0/2/1 | Fε2=1, Mε2=1, Mε3/ε3=1 | ε2=1, ε4=2 | Astrocytes=1, inhibitory=5; 3 | 3 / 6 |

Interpretation of this table:

- `TUFM` and `CHCHD2` have many candidate calls, but every one is
  self-containing. Their recurrence alone is weak evidence that they are
  upstream drivers.
- `ATP5PB` is also always self-containing and never global. `ATP5F1A` and
  `ATP5IF1` have no candidate calls.
- `PARK7` has only six candidate calls, three of which are self-containing.
- The self-independent `APOE`, `LAMTOR5`, and `GABARAPL2` neighborhoods are
  therefore more useful for forming upstream-to-downstream testable models.

## Main limits and recommended manuscript language

- The three claims are **network-supported hypotheses**, not causal chains.
- Repeated fine-cell calls use the same broad network. They show recurrence of
  one fixed topology against different signatures, not repeated inference of
  the edge.
- Phase 11 and Phase 12 reuse the same AD-versus-NCI signatures. Their
  agreement is internal cross-scale consistency, not independent replication.
- Male ε2 has only 7 AD and 6 NCI donors. Its high call burden needs
  donor-level sensitivity analysis before strong sex–APOE claims.
- No formal AD-by-sex, AD-by-APOE, or three-way interaction was fitted. Use
  “observed in the female-ε2 AD-up signature,” not “female ε2 activates.”
- Primary directional counts should lead the manuscript. Secondary pools and
  `AD_both_mito` calls can be presented as supporting sensitivity results.
- For external validation, repeat the analysis with donor pseudobulk
  interaction models, independently inferred or public brain networks, and
  leave-one-donor-out signatures.

Suggested concise wording:

- **APOE:** “APOE was significant in 7 primary astrocyte KDA runs; all 7
  neighborhoods contained `TUFM`, including matched female-ε2 AD-up and
  male-ε2 AD-down `Ast GRM3` signatures.”
- **LAMTOR5:** “LAMTOR5 was significant in 38 primary neuronal runs, and 28
  neighborhoods contained `ATP5IF1`; 15 of these were directional rather than
  derived-union calls.”
- **GABARAPL2:** “GABARAPL2 was significant in 32 primary neuronal runs;
  `CHCHD2` occurred in 25, `PARK7` in 16, and both in 13. The complete module
  was restricted to the excitatory network.”


## Bibliography

- Bar-Peled L, Schweitzer LD, Zoncu R, Sabatini DM. Ragulator is a GEF for the
  Rag GTPases that signal amino acid levels to mTORC1. *Cell*.
  2012;150(6):1196–1208.
  [doi:10.1016/j.cell.2012.07.032](https://doi.org/10.1016/j.cell.2012.07.032).
- Dai X, Ye Z, Wang C, et al. SIK2-mediated phosphorylation of GABARAPL2
  facilitates autophagosome–lysosome fusion and rescues neurodegeneration in an
  Alzheimer's disease model. *Translational Neurodegeneration*. 2025;14:53.
  [doi:10.1186/s40035-025-00514-4](https://doi.org/10.1186/s40035-025-00514-4).
- Esparza-Moltó PB, Romero-Carramiñana I, Núñez de Arenas C, et al. Generation
  of mitochondrial reactive oxygen species is controlled by ATPase inhibitory
  factor 1 and regulates cognition. *PLOS Biology*. 2021;19(5):e3001252.
  [doi:10.1371/journal.pbio.3001252](https://doi.org/10.1371/journal.pbio.3001252).
- Schmukler E, Solomon S, Simonovitch S, et al. Altered mitochondrial dynamics
  and function in APOE4-expressing astrocytes. *Cell Death & Disease*.
  2020;11:578.
  [doi:10.1038/s41419-020-02776-4](https://doi.org/10.1038/s41419-020-02776-4).
- Wang H, Sun HQ, Zhu X, et al. GABARAPs regulate PI4P-dependent
  autophagosome:lysosome fusion. *Proceedings of the National Academy of
  Sciences of the United States of America*. 2015;112(22):7015–7020.
  [doi:10.1073/pnas.1507263112](https://doi.org/10.1073/pnas.1507263112).
- Williams HC, Farmer BC, Piron MA, et al. APOE alters glucose flux through
  central carbon pathways in astrocytes. *Neurobiology of Disease*.
  2020;136:104742.
  [doi:10.1016/j.nbd.2020.104742](https://doi.org/10.1016/j.nbd.2020.104742).
- Zhong B-R, Zhou G-F, Song L, et al. TUFM is involved in Alzheimer's
  disease-like pathologies that are associated with ROS. *The FASEB Journal*.
  2021;35(5):e21445.
  [doi:10.1096/fj.202002461R](https://doi.org/10.1096/fj.202002461R).
- Zhou W, Zhang MM, Tang W, et al. CHCHD2 and CHCHD10 promoted autophagic
  clearance of protein aggregates via GABARAPs. *Autophagy*. 2026:1–30.
  [doi:10.1080/15548627.2026.2678427](https://doi.org/10.1080/15548627.2026.2678427).
