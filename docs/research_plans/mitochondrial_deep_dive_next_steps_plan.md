# Next-step plan: sex/APOE-resolved mitochondrial mechanisms in Alzheimer disease

**Prepared:** 2026-08-07  
**Purpose:** convert the current DEG, pathway, similarity, and KDA results into a focused, statistically defensible biological story with prioritized genes, figures, and cross-validation  
**Status:** proposed plan; analyses below have not yet been run

## 1. Bottom line

The project should not begin with another unrestricted screen of all genes, all pathways, and all 54 cell types. The current work already contains a plausible story, but its most interesting parts remain descriptive or network-predicted.

The recommended central question is:

> Does Alzheimer disease disrupt coordination among mtDNA-encoded respiratory genes, nuclear-encoded OXPHOS/mitochondrial-translation genes, and mitochondrial inner-membrane maintenance programs, and is that disruption modified by sex, APOE, and cell type?

This question is more specific and novel than “mitochondria are altered in AD.” It also connects the strongest existing observations:

- OXPHOS direction differs descriptively across sex/APOE strata.
- Selected male strata may have discordant mtDNA and nuclear OXPHOS responses.
- Female APOE ε4 shows respiratory and redox loss, while APOE ε2 shows the strongest apparent sex reversal.
- Astrocytic `APOE`–`TUFM`, neuronal `LAMTOR5`–`ATP5IF1`, and neuronal `GABARAPL2`–`CHCHD2`/`PARK7` provide three candidate control systems above translation, ATP synthase, and mitochondrial quality control.

The work should proceed in this order:

1. Correct current annotation/ranking/claim issues and make the professor-requested subnetworks.
2. Run donor-level pseudobulk interaction and pathway analyses to determine whether the sex/APOE patterns are real.
3. Test mitonuclear coordination and a small prespecified set of non-OXPHOS mitochondrial programs.
4. Rerun KDA under stricter, non-circular conditions and compare with an independent network method.
5. Add genetics, protein-network/proteomics, and independent-cohort evidence.
6. Advance only candidates that pass predefined evidence gates.

The most defensible current central claim is:

> AD-associated mitochondrial transcription differs descriptively across sex/APOE strata and cell types, while cell-type-matched network analysis nominates distinct candidate systems linked to a recurrent respiratory endpoint.

The next analyses should determine whether this can be strengthened to a donor-level interaction and mitonuclear-coordination conclusion.

## 2. What is already available

### 2.1 Completed analysis chain

The repository contains a well-developed exploratory chain:

- 276 eligible ROSMAP donors: 142 NCI and 134 AD.
- Six sex/APOE strata across 54 fine cell types.
- 321 of 324 planned MAST AD-versus-NCI contrasts were estimable.
- MitoCarta/extended mitochondrial annotation.
- Zhang–Yu-style ternary similarity analysis.
- MitoCarta and MSigDB pathway-tail over-representation analysis.
- 1,782 planned cell-type-matched KDA runs, of which 1,021 were eligible and 840 returned at least one significant candidate.
- 10,172 significant KDA rows and 717 unique candidate genes.
- A more conservative interpretation screen retaining 694 primary directional rows, 200 candidates, and 103 runs.

The principal source is the [joint Phase 11–12 discussion](../analysis/phase11_phase12_joint_mitochondrial_discussion.md). Exact evidence for the three highlighted candidates is in [the selected-connections report](../analysis/phase11_phase12_selected_mitochondrial_connections.md).

### 2.2 Strongest current phenotype

The current threshold-level OXPHOS pattern is:

| Sex/APOE stratum | OXPHOS AD-up occurrences | OXPHOS AD-down occurrences | Current interpretation |
|---|---:|---:|---|
| Female ε2 | 398 | 5 | strongly AD-up |
| Female ε3/ε3 | 319 | 13 | mostly AD-up |
| Female ε4 | 50 | 274 | mostly AD-down |
| Male ε2 | 95 | 564 | strongly AD-down, but least stable stratum |
| Male ε3/ε3 | 85 | 86 | mixed |
| Male ε4 | 141 | 86 | mixed with selected increases |

This pattern remains qualitatively present after excluding mtDNA-encoded genes. The strongest localized ε2 reversal is in `Exc L3-4 RORB CUX2`, and notable ε4 patterns occur in `Exc RELN CHD7` and `Exc L2-3 CBLN2 LINC02306`.

This is currently an observation, not a formal sex or APOE interaction. Male ε2 contains only 7 AD and 6 NCI donors.

### 2.3 Strongest current candidate systems

| Candidate system | Existing support | Most defensible role now |
|---|---|---|
| Astrocytic `APOE` → `TUFM` | Seven primary APOE calls; all seven contain `TUFM`; exact female-ε2-up/male-ε2-down match in `Ast GRM3` | strongest exact pathway-to-network bridge and established AD anchor |
| Neuronal `LAMTOR5` → `ATP5IF1` | 38 primary `LAMTOR5` calls; `ATP5IF1` occurs in 28 primary neighborhoods and 15 primary directional calls | strongest novel nutrient-sensing-to-ATP-synthase hypothesis |
| Excitatory `GABARAPL2` → `CHCHD2`/`PARK7` | 32 primary calls; `CHCHD2` in 25, `PARK7` in 16, both in 13; prior AD-model support for GABARAPL2 | strongest preclinically supported autophagy/mitochondrial-quality-control module |
| `SELENOW` → neuronal redox/respiratory program | 35 primary calls and strong global positioning; published tau/redox perturbation evidence | high-priority validation candidate, somewhat less novel biologically |
| OPC `FTL`/`ANKRD11` → `FTH1`/`GPX4`/respiration | shared OPC iron/redox motif | promising but must distinguish two drivers from one fixed topology |
| `RPL11` → `APOO`/`TOMM7`/`SLIRP` | broad, recurrent and usually global | independent-network and matched-hub validation required before prioritization |
| `PPARGC1B` versus OXPHOS | 11 male-ε2 AD-up contexts despite mostly AD-down male-ε2 OXPHOS | valuable compensation hypothesis outside KDA |

`RPL13` must not be prioritized until the `RPL13`/`MRPL13` synonym-mapping error is corrected.

### 2.4 Non-OXPHOS clues already present

The current similarity-tail analysis contains several useful leads, but it should be treated as hypothesis generation because the high-similarity tails consist mostly of `(0,0)` state pairs.

- Female-versus-male high tail: fusion and TCA-cycle annotations.
- ε2-versus-ε3/ε3 high tail: protein import/sorting, mitochondrial proteases, and preprotein cleavage.
- Female-versus-male within ε4 low tail: ROS and glutathione metabolism.
- Across divergent tails: OXPHOS, Complex I, Complex IV, Complex V, and sometimes permeability-transition-pore annotations.

These provide a prespecified shortlist for continuous donor-level pathway tests. They are not yet evidence that the pathways are activated or suppressed in a group.

## 3. Corrections required before the next presentation or figure release

These are scientific corrections, not cosmetic edits.

1. **Use the current methods, not the July slide deck.** The older presentation says age and PMI were not used; the production MAST models included `nCount_RNA`, scaled age at death, and scaled PMI.
2. **Correct the APOE call-direction statement.** The seven primary astrocyte `APOE` calls comprise one AD-up, three AD-down, and three derived `AD_both_mito` calls. They are not all downregulated. ATP-synthase genes occur in the down/union neighborhoods, not in the female-ε2 AD-up APOE result.
3. **Correct the LAMTOR5 scope.** Primary `LAMTOR5`–`ATP5IF1` support is concentrated in female ε2, female ε4, and male ε2; it is not supported in all six primary strata.
4. **Correct the GABARAPL2 scope.** The complete `GABARAPL2`–`CHCHD2`/`PARK7` module is mainly excitatory, and female ε3/ε3 has no primary `GABARAPL2` call.
5. **Describe the KDA background exactly.** It is the genes tested in the exact expression contrast intersected with the induced matching network, not simply every node in the original network.
6. **Do not call repeated fine-cell KDA calls independent replication.** Fine cell types reuse broad networks, pooled signatures reuse primary data, and `AD_both_mito` is derived from directional signatures.
7. **Repair `RPL13`/`MRPL13` mapping and rerun affected outputs.** Stable identifiers should take priority over ambiguous synonym matching.
8. **Do not rank drivers from significant KDA rows alone.** Mean negative-log-P ranking requires the complete candidate-by-run matrix, including nonsignificant tests.

## 4. Proposed biological model

The proposed working model is:

```text
sex/APOE and disease state
          ↓
cell-specific control system
          ↓
mitochondrial translation / ATP synthase / quality control
          ↓
coordination or imbalance between mtDNA and nuclear programs
          ↓
respiratory-chain and AD-related cellular phenotype
```

The three highlighted candidate systems fit this model:

- Astrocytes: `APOE` → `TUFM`, `LDHB`, `CHCHD10`, and an ATP-synthase subnetwork.
- Neurons: `LAMTOR5` → `ATP5IF1` and ATP-synthase regulation.
- Excitatory neurons: `GABARAPL2` → `CHCHD2` and a longer path to `PARK7`, linking autophagic flux and mitochondrial stress control.

The model also follows the related Mathys work, which highlights nuclear OXPHOS, mitochondrial translation/tRNA-synthetase programs, and mitochondrial inner-membrane/MIB-MICOS genes such as `DNAJC11`, `CHCHD3`, `CHCHD6`, and `IMMT`.

The arrows above are hypotheses. Existing Bayesian-network edges are unsigned predictions and do not demonstrate molecular causality.

## 5. Prespecified questions and hypotheses

### Q1. Are mitochondrial genes more altered than comparable non-mitochondrial genes?

**H1:** In selected AD-versus-NCI contrasts, MitoCarta genes have greater directional effect burden than expression-, detection-, and gene-length-matched non-MitoCarta genes.

This directly answers the professor's request to determine when mitochondrial changes are more profound than non-mitochondrial changes.

### Q2. Does AD interact with sex or APOE at the pathway level?

**H2a:** The AD effect on OXPHOS differs between females and males within APOE ε2 and/or ε4.

**H2b:** The AD effect on mitochondrial programs differs between ε4 and ε3/ε3 within sex.

**H2c:** APOE ε2 shows a distinct, but potentially fragile, sex-dependent program rather than a universal protective response.

These must be tested with direct difference-of-differences contrasts. “Significant in one group but not another” is not an interaction.

### Q3. Is mitonuclear coordination altered?

**H3:** AD changes the coordination among:

- mtDNA-encoded ETC transcripts;
- nuclear-encoded OXPHOS subunits;
- mitochondrial translation/mitoribosome genes; and
- MIB/MICOS/inner-membrane organization genes.

The direction and magnitude of this imbalance may differ by sex, APOE, and cell type. Male ε3/ε3 and male ε4 are particularly relevant because current aggregate summaries show nuclear OXPHOS decreases with relative mtDNA increases.

### Q4. Which non-OXPHOS programs are genuinely group-specific?

**H4:** At least one of fatty-acid oxidation, TCA/pyruvate metabolism, mitochondrial import/proteostasis, mitophagy/dynamics, ROS/glutathione metabolism, or iron/heme metabolism shows a formal sex/APOE interaction that is not explained by OXPHOS gene overlap.

### Q5. Which KDA candidates remain credible after removing circularity and network bias?

**H5:** `APOE`, `LAMTOR5`, and `GABARAPL2` remain above matched null expectations when query genes are excluded from the candidate-driver set before testing, primary directional runs are analyzed alone, layer selection is corrected, and alternative networks are used.

### Q6. Which candidates have independent human evidence?

**H6:** The best candidates show concordant evidence in at least two independent layers beyond the discovery MAST→KDA chain, such as donor-pseudobulk interaction, independent transcriptomic replication, AD genetics/QTL, proteomics, or a protein/alternative regulatory network.

## 6. Priority order

| Priority | Work package | Why it comes now | Go/no-go output |
|---:|---|---|---|
| P0 | Result/annotation audit and requested figures | prevents known overstatements and addresses the professor's immediate request | corrected claim table, corrected annotation, three subnetwork figures |
| P1 | Full donor-level pseudobulk interactions | decides whether the sex/APOE story is real | interaction estimates, confidence intervals, stability results |
| P1 | Continuous pathway and mitonuclear analysis | gives a deeper result beyond DEG counts and OXPHOS labels | signed pathway effects and mitonuclear imbalance/coupling |
| P2 | KDA robustness and alternative networks | decides which predicted drivers deserve attention | robust driver ranks and empirical-null calibration |
| P3 | Genetics, protein, and independent cohort | supplies evidence not inherited from the same DEG chain | evidence matrix and replicated/demoted candidates |
| P4 | Experimental proposal | only justified after computational gates | 3–5 candidate–mediator pairs with assays |

## 7. Work package P0: freeze, correct, and visualize the current results

### 7.1 Freeze an auditable result set

Create a small analysis-freeze manifest containing:

- commit or code-bundle hash;
- configuration hashes;
- DEG, pathway, and KDA input/output hashes;
- MitoCarta, HGNC, GENCODE, and MSigDB versions;
- exact primary versus secondary run definitions;
- the six donor counts and fine-cell eligibility counts;
- a record of known corrections.

Do not modify the existing production result files in place. Corrected analyses should write to a new versioned output directory.

### 7.2 Repair gene identifiers

Use stable HGNC/Ensembl identifiers as the primary join key. Specifically:

1. Separate `RPL13` from `MRPL13`.
2. Identify every DEG signature and KDA run affected by ambiguous synonym mapping.
3. Regenerate Phase 09 signatures and affected Phase 12 runs.
4. Produce a before/after table of query sizes, candidates, and ranks.
5. Audit other cytosolic/mitochondrial ribosomal synonym collisions using the same rule.

### 7.3 Produce the requested layer-3 subnetworks

Generate three driver-centered deliverables containing five topology panels:

| Driver | Network panel(s) | Existing layer-3 size | Mitochondrial DEG nodes currently expected |
|---|---|---:|---:|
| `APOE` | Astrocytes | 58 nodes, 57 edges | 7 |
| `LAMTOR5` | Excitatory and inhibitory | 54/56 and 62/62 nodes/edges | 17 and 15 |
| `GABARAPL2` | Excitatory and inhibitory | 51/51 and 16/15 nodes/edges | 13 and 1 |

Recommended encodings:

- topology rings or columns for layer 0, 1, 2, and 3;
- driver as a gold diamond;
- node fill as signed AD log2 fold change in the displayed exact contrast;
- node size as within-panel out-degree or total subnetwork connectivity;
- thick outline for genes contributing to the significant KDA overlap;
- shape or small glyph for MitoCarta pathway class;
- explicit label/star for ATP-synthesis/transport genes;
- gray for non-DEG intermediary genes;
- arrows labeled in the caption as inferred topology, not activation/inhibition.

Do not merge excitatory and inhibitory edges. Use separate facets because they are different fitted networks.

The clearest contrast-specific panels are:

- `APOE`, `Ast GRM3`: female ε2 AD-up versus male ε2 AD-down.
- `LAMTOR5`: female ε2 AD-up, female ε4 AD-down, and male ε2 AD-down in the best-supported excitatory subtypes.
- `GABARAPL2`: female ε2, female ε4, and male ε2 in superficial/RORB excitatory subtypes.

Export:

- composite SVG/PDF/PNG;
- one standalone figure per driver;
- Cytoscape-ready node and edge TSVs;
- a node-validation table with layer, DEG direction, log2FC, KDA-overlap membership, and pathway annotations;
- a methods/caption Markdown file.

### 7.4 Replace or demote the current circular plot

The current circular plot is dominated by mtDNA structural genes and combines primary, pooled, and derived signatures. It is not a clean key-driver ranking.

For a corrected supplementary circular plot:

1. Export the complete candidate-by-run P-value matrix, including nonsignificant candidates.
2. Restrict the primary display to exact primary `AD_up_mito` and `AD_down_mito` runs.
3. Exclude pooled and `AD_both_mito` calls from the main ranking.
4. Calculate mean `-log10(P)` across the relevant runs for each candidate and network. The log base changes the score scale, not the rank.
5. Report ACAT as a sensitivity ranking if desired.
6. Separate networks and/or sex/APOE groups rather than encoding everything in concentric tracks.
7. Remove mtDNA genes from the candidate-driver ranking while retaining them as downstream signature genes.
8. Use a compact legend and a color-blind-safe palette.

For the main paper/presentation, prefer a driver-by-context dot heatmap:

- rows: prioritized candidates;
- columns: six primary sex/APOE strata;
- facets: broad network;
- dot size: corrected evidence strength;
- fill: direction of the downstream signature;
- outline: global versus local candidate or external validation status.

## 8. Work package P1: donor-level pseudobulk confirmation

### 8.1 Use the existing implementation

The repository already contains the essential production logic:

- [pseudobulk construction](../../scripts/07_make_pseudobulk.R)
- [contrast manifest](../../scripts/07_build_contrast_manifest.R)
- [edgeR quasi-likelihood testing](../../scripts/07_run_pseudobulk_de.R)

The contrast manifest already defines:

- six AD-versus-NCI effects;
- three AD-by-sex contrasts, one within each APOE group;
- four AD-by-APOE contrasts, ε2 or ε4 versus ε3/ε3 within each sex;
- an omnibus heterogeneity test.

Only a local vasculature pilot is currently present. The next computational step is to run the full production pseudobulk workflow across the available RDS objects on Minerva, not to rewrite the analysis from scratch.

### 8.2 Primary statistical unit and model

Use raw UMI counts summed within donor × fine cell type. The donor is the biological replicate.

Primary model per fine cell type:

```text
~ 0 + diagnosis_sex_APOE_group + age_at_death + PMI
```

Use edgeR quasi-likelihood with robust dispersion estimation and `filterByExpr`. Add batch/RIN or other technical covariates only if available, sufficiently complete, and not collinear with the six groups.

Primary eligibility:

- at least 20 nuclei per donor/fine cell type;
- at least 5 eligible donors per required group;
- preferably at least 10 per group for headline gene-level conclusions.

Sensitivity:

- 50-nucleus donor threshold;
- broad-cell pseudobulk for strata that are too sparse at fine resolution;
- nucleus subsampling within donor to check depth imbalance;
- no minimum-cell threshold selected after looking at P values.

### 8.3 Add explicit three-way contrasts selectively

Add two interpretable 1-degree-of-freedom contrasts where sample counts permit:

```text
[AD effect in female ε4 − AD effect in male ε4]
− [AD effect in female ε3/ε3 − AD effect in male ε3/ε3]

[AD effect in female ε2 − AD effect in male ε2]
− [AD effect in female ε3/ε3 − AD effect in male ε3/ε3]
```

These ask whether the sex modification of AD differs by APOE background. The ε2 three-way contrast is expected to be low powered and should be primary only in cell classes that retain sufficient donors; otherwise label it exploratory.

### 8.4 Analyze broad cell classes before all fine types

Start with the cell systems that directly test the current model:

1. Astrocytes, especially `Ast GRM3`.
2. Excitatory neurons, especially `Exc L3-4 RORB CUX2`, `Exc RELN CHD7`, and `Exc L2-3 CBLN2 LINC02306`.
3. Inhibitory neurons with supported `LAMTOR5` paths.
4. OPCs.
5. `Mic P2RY12`/microglia.
6. Endothelial/vasculature as a lower-priority contrast.

Run all 54 fine types for completeness, but declare the cell systems above as the primary multiple-testing family before examining results.

These cell systems were selected using the current exploratory results from the same donors. Pseudobulk therefore supplies donor-aware internal confirmation, not an independent confirmatory cohort. The selection process must be disclosed, and external replication remains necessary.

### 8.5 Stability analyses

For every headline effect:

- leave one donor out;
- bootstrap donors within the six groups;
- downsample larger strata to match the smaller stratum's donor and nucleus distributions;
- record sign consistency, median effect, confidence interval, and maximum donor influence;
- compare pseudobulk effect direction with MAST, treating agreement as method consistency rather than replication.

The male-ε2 result should advance only if:

- no single donor changes the sign of the primary pathway effect;
- at least 80% of donor bootstraps retain the same direction;
- the effect remains materially larger than the matched null under donor/nucleus downsampling;
- confidence intervals are shown even when FDR is not significant.

If those criteria fail, male ε2 should be described as an exploratory high-effect/low-power stratum rather than the main conclusion.

This is especially important because the related Yu power analysis found very limited power for small/moderate effects in male ε2. Stability and effect-size uncertainty are more informative here than a binary P-value threshold.

## 9. Work package P1: continuous pathways and mitochondrial-versus-non-mitochondrial burden

### 9.1 Primary pathway collection

Use MitoCarta MitoPathways as the primary collection because it is prespecified and mitochondria-specific. Use MSigDB C2:CP secondarily for broader context.

Prespecify the following pathway families:

1. OXPHOS overall and complexes I–V separately.
2. mtDNA-encoded ETC versus nuclear-encoded OXPHOS.
3. ATP synthase/ATP transport.
4. Mitochondrial translation, mitoribosome, and tRNA synthetases.
5. Protein import, sorting, cleavage, and proteases.
6. MIB/MICOS and inner-membrane organization.
7. Dynamics, mitophagy, and quality control.
8. Fatty-acid oxidation and ketone/lipid metabolism.
9. TCA/pyruvate metabolism.
10. ROS/glutathione and iron/heme metabolism.

Collapse redundant parent/child annotations for figures. Do not present multiple overlapping neurodegeneration pathway names as independent mechanisms when their overlap is the same ETC genes.

### 9.2 Use full ranked statistics

Run a direction-aware competitive gene-set test on the full pseudobulk statistics rather than thresholded DEG lists.

- Primary: `camera` or another method that accounts for inter-gene correlation.
- Sensitivity: `fgseaMultilevel` on a signed statistic.
- Report signed pathway effect/NES, confidence or test statistic, gene count, and FDR.
- Use the exact tested transcriptome as background.

Apply hierarchical FDR:

1. primary pathway × prespecified cell system × planned interaction tests;
2. genes within a significant module;
3. all 54 fine-cell results as a broader sensitivity family.

### 9.3 Formally compare mitochondrial and non-mitochondrial genes

For each primary contrast, calculate:

1. the odds ratio for a tested MitoCarta gene being a threshold-level DEG relative to a tested non-MitoCarta gene;
2. the difference in median absolute signed statistic or absolute log2FC;
3. direction-specific enrichment for AD-up and AD-down genes.

Raw odds ratios are not sufficient because mitochondrial genes differ in expression and detectability. Construct 1,000–10,000 matched non-mitochondrial gene sets matched on:

- mean expression;
- detection rate;
- gene length;
- GC content if available;
- network degree for analyses tied to KDA.

Report the empirical percentile and P value of the observed mitochondrial burden. A cell type/stratum should be called “mitochondrially enriched” only if the competitive and matched-null analyses agree.

### 9.4 Define “sex-specific,” “APOE-specific,” “common,” and “cell-type-specific” in advance

- **Sex-modified AD pathway:** direct AD-by-sex contrast FDR below the prespecified threshold within an APOE group.
- **APOE-modified AD pathway:** direct ε2-versus-ε3/ε3 or ε4-versus-ε3/ε3 AD-effect contrast passes FDR within sex.
- **Three-way modification:** the difference in sex modification between APOE groups passes the three-way contrast.
- **Common response:** same-direction meta-analyzed AD effect across groups with no material heterogeneity; not merely significant in several groups.
- **Cell-type-specific response:** significant cell-type heterogeneity and a stable effect in the nominated cell type; not absence of significance elsewhere.
- **ε2-unique pathway:** direct ε2-versus-ε3/ε3 interaction plus a stable ε2 effect. Significance only in ε2 is insufficient.

## 10. Work package P1: mitonuclear coordination and continuous disease phenotypes

### 10.1 Construct four donor-level modules

Within each selected cell type, calculate donor-level scores for:

1. mtDNA-encoded ETC genes;
2. nuclear-encoded OXPHOS genes, with complex-specific scores;
3. mitochondrial translation/mitoribosome/tRNA-synthetase genes;
4. MIB/MICOS/inner-membrane genes, including `DNAJC11`, `CHCHD3`, `CHCHD6`, and `IMMT` when measured.

Use mean standardized logCPM as the transparent primary score and the first principal component as a sensitivity. Require a minimum proportion of measured genes and report score reliability.

Use several literature-supported genes as benchmarks rather than automatically adding them to the novel-candidate list:

- `AHNAK` as a previously validated astrocyte-network key-driver positive control from the Wang framework;
- `PRDX6` and `NDUFS1` as protein-level redox/OXPHOS comparators;
- `CLU`, `LINGO1`, and heat-shock genes as sex/APOE-response comparators;
- `DNAJC11`, `CHCHD3`, `CHCHD6`, and `IMMT` as inner-membrane/MIB-MICOS sentinels.

### 10.2 Define imbalance without relying on one arbitrary scale

Use two complementary endpoints:

1. standardized module difference:

```text
mitonuclear imbalance = Z(mtDNA ETC score) − Z(nuclear OXPHOS score)
```

2. NCI-reference coupling residual:

```text
fit mtDNA ETC score ~ nuclear OXPHOS score in eligible NCI donors
apply the reference relation to every donor
use the residual as excess or deficient mtDNA expression relative to nuclear OXPHOS
```

Also test whether the mtDNA-versus-nuclear slope/correlation changes by disease, sex, or APOE. Agreement among the difference, residual, and coupling-slope analyses is stronger than any one metric.

### 10.3 Technical sensitivity

Mitochondrial RNA is biologically relevant here, so do not automatically regress out percent mitochondrial reads in the primary model. Instead:

- report mitochondrial read fraction separately;
- repeat the model with mitochondrial read fraction and available quality measures as sensitivity covariates;
- exclude flagged low-quality donors/cell-type profiles;
- separate mtDNA from nuclear effects;
- test whether results persist after removing all mtDNA genes;
- add mtDNA copy number or mitochondrial-mass information if it becomes available.

### 10.4 Use pathology and cognition already present in the cohort table

The resolved cohort contains Braak, CERAD, amyloid, tau/tangle, MMSE, and longitudinal cognitive variables. These can provide a deeper phenotype without obtaining a new expression dataset.

Secondary analyses should test whether module and imbalance scores associate with:

- Braak stage;
- amyloid and tangle burden;
- last MMSE/global cognition or a prespecified cognitive composite;
- cognitive decline slope;
- cognitive resilience defined as cognition better or worse than expected from pathology, following a prespecified Mathys-style residual model.

Run these in all eligible donors for power, then test sex/APOE modification. Avoid describing cross-sectional association as mediation or causality.

## 11. Work package P2: KDA robustness and alternative networks

### 11.1 Correct the primary KDA analysis set

For the main analysis:

- use only exact primary `AD_up_mito` and `AD_down_mito` signatures;
- keep pooled and `AD_both_mito` results supplementary;
- require at least 10 effective query genes;
- exclude every effective query gene from the candidate-driver set before testing;
- exclude mtDNA structural genes from the candidate-driver set;
- retain non-mitochondrial upstream candidates;
- use exact contrast-tested genes intersected with the matching network as background.

This changes the test itself and is preferable to filtering circular rows after significance has already been calculated.

### 11.2 Correct layer and multiplicity handling

Current KDA selects the best of layers 1–3. Reanalyze with:

- fixed layer 1, 2, and 3 results;
- correction across candidate × layer tests within a run, or an empirical max-statistic procedure;
- a study-wide sensitivity FDR across primary runs;
- complete P-value output for every tested candidate, including nonsignificant candidates.

The within-run BH P value can remain the primary KDA statistic, but the cross-run and layer sensitivities must be shown for candidate ranking.

### 11.3 Matched empirical nulls

For every query, generate null signatures matched on:

- query size;
- expression and detection;
- mitochondrial annotation composition;
- mtDNA fraction;
- network degree distribution.

Repeat KDA on at least 1,000 nulls for focal runs. Report empirical candidate frequency and rank rather than only hypergeometric fold enrichment.

### 11.4 Network stability

Test:

- removal of low-support edges if edge-support files can be obtained;
- modest edge deletion/reversal perturbations;
- fixed broad-network reuse versus independently inferred networks;
- gene-filter sensitivity (`min.pct` 10%, 5%, and 1%) first in the focal cell types and contrasts;
- core MitoCarta versus the broader mitochondrial-related query universe.

Only run a full 54-cell rerun at every `min.pct` if the focal analysis shows material rank instability. Otherwise retain the Yu-compatible 10% threshold as primary and report focused sensitivity results.

### 11.5 Alternative network evidence

Use at least two alternatives:

1. **Donor-pseudobulk coexpression/MEGENA network.** Build broad-cell networks first; build a fine-cell network only if donor and gene coverage support stable modules. Treat it as undirected corroboration, not causal direction.
2. **Protein/PPI or public AD network.** Use a curated interaction network and, if obtainable, the protein coexpression/Bayesian networks associated with the Wang multiscale study.

For MEGENA:

- filter low-count and low-prevalence genes before inference;
- use donor-level normalized expression, not individual nuclei;
- adjust technical covariates;
- bootstrap donors and report module/edge preservation;
- test whether candidate modules are enriched for the same mitochondrial signature.

For PPI/network proximity, use degree-matched randomization because well-studied hubs otherwise receive an automatic advantage.

### 11.6 Driver ranking

Do not let repeated pooled KDA calls dominate the ranking. Require two gates:

**Gate A: phenotype support**

- donor-level effect or interaction in the candidate's cell context; and
- a stable mitochondrial module containing the predicted mediator/readouts.

**Gate B: robust topology**

- candidate-self-independent primary KDA;
- survival of matched-null/layer sensitivity; and
- support in an alternative network or protein interaction analysis.

After the gates, score independent evidence layers:

| Evidence layer | Suggested score |
|---|---:|
| Donor-level interaction/pathway support | 0–2 |
| Robust KDA across sensitivity analyses | 0–2 |
| Independent/alternative network support | 0–2 |
| Independent transcriptomic replication | 0–2 |
| AD GWAS/fine-mapping/QTL support | 0–2 |
| Protein/proteomic support | 0–2 |
| Prior perturbation evidence | 0–2 |
| Cell specificity and experimental tractability | 0–1 |

Keep `APOE` as an established anchor and rank novel candidates separately so that the APOE locus does not trivially dominate the novel-target list.

## 12. Work package P3: genetics and QTL integration

Use a frozen, lab-approved release of AD GWAS summary statistics from NIAGADS or another primary consortium source. Record ancestry, phenotype definition, genome build, sample size, and accession.

Recommended analyses:

1. Gene-level association for every robust candidate and mediator.
2. Enrichment of the robust KDA candidate set relative to expression- and degree-matched network genes.
3. Fine-mapped credible-set overlap rather than nearest-gene assignment alone.
4. Colocalization with brain or cell-type eQTL/sQTL/pQTL when available.
5. Candidate-pathway enrichment across AD risk loci.
6. A sensitivity excluding the extended APOE/TOMM40 locus so that one strong region does not determine the result.

Interpretation rules:

- GWAS locus proximity is supporting evidence, not proof that the candidate is the causal gene.
- Colocalization is stronger than a shared broad locus.
- Absence of common-variant GWAS evidence does not refute a regulatory candidate.
- Sex-stratified genetics should be used only if the discovery GWAS is adequately powered and independent of the expression cohort.

Useful current portals include [NIAGADS](https://www.niagads.org/genomics/) for AD genetics and [Agora](https://agora.adknowledgeportal.org/) for integrated human transcriptomic, proteomic, metabolomic, genetic, and target-nomination evidence.

## 13. Work package P3: protein and multi-omic evidence

### 13.1 Human proteomics

Check whether each candidate and mediator is measured in:

- ROSMAP brain proteomics/phosphoproteomics;
- MSBB parahippocampal-gyrus proteomics;
- BLSA PFC proteomics;
- Wang protein modules/networks;
- Agora gene-level evidence.

For measured proteins, test:

- AD association and direction;
- sex/APOE interaction where sample size permits;
- association with amyloid, tau, cognition, and resilience;
- correlation with the matching mitochondrial protein/module;
- membership or proximity in protein coexpression modules.

ROSMAP proteomics from overlapping donors is orthogonal modality support, not independent-cohort replication. MSBB/BLSA can provide more independent cross-cohort evidence.

### 13.2 Chromatin/QTL support

For candidates that survive transcript/network tests, ask whether cell-type chromatin-accessibility or enhancer–gene links support regulation of the predicted module. Prioritize evidence in the matching astrocyte, excitatory-neuron, inhibitory-neuron, OPC, or microglial context.

This layer is particularly useful for `WDR82`, `ANKRD11`, and other chromatin-linked candidates. It is not required for every candidate.

## 14. Work package P3: independent expression validation

### 14.1 Validation ladder

Use the following terminology:

1. **Internal method consistency:** MAST versus donor pseudobulk.
2. **Internal stability:** bootstrap, leave-one-donor-out, or split-half within ROSMAP.
3. **Region/assay generalization:** multi-region Mathys/ROSMAP data or another assay with overlapping donors.
4. **Independent cohort replication:** a separate donor cohort.
5. **Orthogonal modality support:** protein, chromatin, genetics, or perturbation.

Do not call levels 1–3 independent replication.

### 14.2 Preferred independent cohort

SEA-AD is the preferred independent single-nucleus validation resource because it provides an independent AD donor series with fine cell annotation and continuous pathology. Before committing, verify:

- donor-level sex and APOE availability;
- sufficient donor counts in each intended group;
- brain-region and phenotype compatibility;
- mapping from ROSMAP fine types to SEA-AD subclasses.

Primary replication should occur at the broad-cell/module level because exact fine-type labels and AD/NCI definitions differ. Use the same frozen gene sets and no rediscovery in SEA-AD.

If APOE-stratified replication is underpowered, test:

- OXPHOS/mitonuclear effect direction across pathology;
- astrocyte `APOE`–`TUFM` coherence;
- neuronal `LAMTOR5`/`ATP5IF1` and `GABARAPL2`/`CHCHD2`/`PARK7` module behavior;
- effect correlations across matched broad cell classes.

The [SEA-AD resource and code](https://github.com/AllenInstitute/SEA-AD_2024) can be used to identify the appropriate processed matrices and taxonomy mapping.

### 14.3 Additional validation datasets

- The available six-region Mathys processed data can test region generalization, but donor overlap must be checked.
- The MSBB parahippocampal-gyrus bulk resource used by Yu can test bulk directional/module replication, with deconvolution or cell-marker adjustment where feasible.
- BLSA/MSBB proteomics can test the protein endpoint.

### 14.4 Replication criteria

For a prespecified module/candidate:

- same direction of effect;
- confidence interval and standardized effect reported;
- significant pathway/module test or concordant effect under a predefined meta-analysis;
- no requirement that every individual DEG pass the same threshold;
- cell-type mapping and phenotype differences documented.

Use discovery-versus-validation scatter plots, sign tests, and random-effects meta-analysis. Do not validate only by overlapping significant gene lists.

## 15. Figure plan

The proposed figure package deliberately borrows the **analytical and visual grammar** of the three related papers, while using this project's own hypotheses, models, and data. These should be described as project-specific analogues or as layouts “inspired by” the cited panels—not as exact reproductions. Exact numerical reproduction would generally be inappropriate because the papers use different phenotypes, cohorts, regions, and (for Wang) proteomic and perturbation data.

Feasibility labels used below:

- **Now:** can be drafted from results already present in the repository, although a discovery-only panel may later be replaced by its donor-aware version.
- **After P1:** requires the donor-pseudobulk and interaction analyses in Priority 1.
- **External:** requires an independent cohort, proteomics, or an alternative published network.
- **Experimental:** requires new wet-lab perturbation data and cannot be presented as a result yet.

### 15.1 Paper-inspired figure crosswalk

#### Mathys single-cell atlas

| Source figure/panel | Reusable analytical idea | Project-specific analogue | Plan destination | Feasibility |
|---|---|---|---|---|
| Fig. 1A–C | Cohort workflow, group composition, and donor-metadata overview | Focused ROSMAP workflow; six sex–APOE groups; donor counts and pathology/cognition coverage | Fig. 1 | Now |
| Fig. 2A and 2F–H | Cell-type-by-trait DEG burden plus overlap/concordance across traits and cell types | Mitochondrial-versus-matched-non-MT burden; concordance across sex/APOE contrasts; clearly separate same-direction from opposite-direction effects | Figs. 2–3 and supplement | Now for MAST; After P1 for confirmation |
| Fig. 3A–B and 3G–H | Pathway summary paired with signed gene-by-cell-type heatmaps; focused mitochondrial-complex panel | Signed pathway landscape plus nuclear OXPHOS, mtDNA ETC, mitochondrial translation, and MIB/MICOS gene panels | Figs. 3–4 | Now for discovery; After P1 for confirmation |
| Fig. 4A–C | Protein-complex module scores across cell types/regions with orthogonal bulk/protein support | Donor-level OXPHOS-complex, ATP-synthase, mitochondrial-translation, and MIB/MICOS scores, followed by RNA/protein validation | Figs. 4 and 8 | After P1; External for protein support |
| Fig. 5A–G | Early-versus-late disease changes, donor module-score boxplots, and PFC-to-MTG confirmation | Test whether mitochondrial programs change early, late, monotonically, or non-monotonically across pathology; compare ROSMAP with SEA-AD/another region | Fig. 4D and validation supplement | After P1; External for cross-cohort panel |
| Fig. 6A–E | Cognitive-trait heatmaps and gene-level correlates | Relate mitochondrial modules and prioritized mediators to cognition and pathology-adjusted cognitive resilience | Fig. 4D and Fig. 8 | After P1 |
| Fig. 7A–F | Donor-aware cell-composition changes | Sensitivity panel testing whether headline mitochondrial effects track loss/expansion of the relevant cell subtype | Supplement/confounder audit | After P1 |
| Fig. 7K/M/O | Cognitively intact versus demented donors within pathologic AD | Compare mitochondrial module/imbalance scores in resilient versus demented donors; use continuous pathology-adjusted cognition as the primary model and grouped boxes for display | Fig. 4D or focused resilience supplement | After P1 |

The most directly useful Mathys-style main panel is the signed mitochondrial gene-by-cell-type heatmap modeled on Fig. 3G–H. Prefer fill for effect size and a glyph for FDR, and pair it with donor-level module estimates rather than showing signed significance alone. For progression, model continuous pathology (and a spline if justified) as primary; use early/middle/late bins only for display.

The local 276-donor metadata support Braak, CERAD, global pathology, amyloid, NFT/tangle, last MMSE, and several longitudinal slopes. They can support an approximate resilience analysis, but the exact 17-test global cognitive composite used by Mathys is not currently present. Either obtain the fuller metadata or label the MMSE/slope-based phenotype transparently; do not imply an exact phenotype reproduction.

#### Yu sex–APOE study

| Source figure/panel | Reusable analytical idea | Project-specific analogue | Plan destination | Feasibility |
|---|---|---|---|---|
| Fig. 1A–B | AD-up and AD-down DEG-count heatmaps across 54 cell types and six sex–APOE strata | Retain as the discovery overview, add donor counts, and add mitochondrial enrichment relative to matched non-MT genes | Fig. 2 and supplement | Now |
| Fig. 1C–E | Common, unique, and opposite response counts | Formalize the most interesting female-versus-male and APOE contrasts and display effect estimates rather than threshold counts alone | Fig. 3 | Now descriptively; After P1 confirmatorily |
| Fig. 2 | Similarity-score distributions | Compact quality-control panel showing where mitochondrial genes sit in the full score distribution | Supplement | Now |
| Figs. 3–5 | Ranked concordant/divergent gene heatmaps paired with pathway dot plots | Retain the intuitive gene-plus-pathway layout, but use continuously ranked pathway tests and explicitly distinguish `(0,0)` concordance from shared directional change | Fig. 3 and supplement | Now; After P1 for primary claims |
| Fig. 6A–B | Sex divergence within each APOE genotype | Core interaction heatmap for ε2, ε3/ε3, and ε4, with donor-aware AD-by-sex estimates and mitochondrial pathways beyond OXPHOS | Fig. 3 | After P1 |
| Fig. 7 | One interpretable gene shown across cell subclusters and all six groups | Small-multiple panels for `TUFM`, `ATP5IF1`, `CHCHD2`, `PARK7`, and any newly supported gene, using donor-level expression/module effects | Figs. 5–6 or supplement | After P1 |

Several Yu-style figures already exist because the current project uses the same six strata and similarity framework. They are useful discovery figures, but rerunning or restyling them is not cross-validation. The publishable advance is to add formal interactions, continuous pathway statistics, male-ε2 stability, and non-MT benchmarking.

Specifically, the current outputs already include [Yu Fig. 1-style panels](../../results/figures/figure01/) and [Yu Figs. 3–6-style panels](../../results/figures/figures03_to_06/). The underlying Phase 08 production table exactly matches all 118,297 rows in Yu Supplementary Table S1, including direction; the Fig. 1 checks pass 16/16, and the Figs. 3–6 status is `validated_complete` with zero failed checks. Thus, these are completed and validated discovery analogues—not merely proposed mockups. They should be retained, clearly labeled as discovery, and upgraded rather than rebuilt from scratch.

#### Wang multiscale modeling study

| Source figure/panel | Reusable analytical idea | Project-specific analogue | Plan destination | Feasibility |
|---|---|---|---|---|
| Fig. 1A–B | End-to-end computational/experimental workflow | snRNA-seq DEG → donor confirmation → mitochondrial pathway → robust KDA → genetics/protein/replication → perturbation gate | Fig. 1 | Now |
| Fig. 2A–F | Volcano plots, signature counts/intersections, APOE-stratified candidate expression | Selected-contrast volcano plots and donor-level candidate/module plots across sex–APOE groups; keep only panels that advance a specific hypothesis | Figs. 2–3 and supplement | Now/After P1 |
| Fig. 3A–F | Cross-cohort signature overlap, GSEA, and RNA–protein concordance | Discovery-versus-validation effect scatter, frozen-set GSEA, sign concordance, and RNA–protein agreement for mitochondrial modules/candidates | Fig. 8 | External |
| Fig. 4A–E | Global coexpression modules, cell-type/function tracks, and a multiscale subnetwork | Alternative donor-pseudobulk modules enriched for mitochondrial biology; annotate cell type, sex/APOE, pathway, and DEG direction | Figs. 7–8 | After P1; External for protein network |
| Fig. 5A–E | Module preservation and evidence-rich module subnetworks | Preserve modules/candidate ranks across Bayesian, coexpression, PPI/protein, and independent-cohort networks; show “not tested” separately from no support | Figs. 7–8 | External |
| Fig. 6A–E | Global Bayesian causal network and key-driver-centered subnetworks | Three requested layer-3 networks centered on `APOE`, `LAMTOR5`, and `GABARAPL2`; color nodes by signed AD effect, size by connectivity, enlarge robust KDs, and label mitochondrial mediators | Fig. 6 | Now |
| Fig. 7A–F | Candidate perturbation workflow, molecular/functional readouts, neighborhood GSEA, and pathway map | Pre-specify the validation design for the best candidate–mediator pair. Show actual knockdown, pTau, respiration, activity, or perturbation-GSEA panels only after those data exist | Conditional experimental figure | Experimental |

The Wang Fig. 6 analogue is the fastest high-value paper-inspired figure: it directly answers the professor's request for three candidate-centered layer-3 subnetworks. Wang Fig. 3 and Fig. 5 analogues are the strongest later cross-validation figures, but they require genuinely orthogonal data or networks.

### 15.2 Paper-analogue build order

1. **Immediate, using existing results:** retain/export the validated Yu analogues; create the Mathys Fig. 3G–H-style mitochondrial effect heatmap; create the Wang Fig. 6-style `APOE`, `LAMTOR5`, and `GABARAPL2` layer-3 subnetworks.
2. **After donor-pseudobulk models:** replace threshold-only comparisons with Yu Fig. 6-style formal interaction estimates; add Mathys Fig. 4/5-style complex scores, continuous pathology trajectories, and resilience panels; add male-ε2 bootstrap/downsampling stability.
3. **After acquiring orthogonal data:** add Mathys Fig. 3D/4B–C-style SEA-AD and protein confirmation plus Wang Fig. 3/5-style cross-cohort concordance and module/driver preservation.
4. **Only after perturbation experiments:** add a Wang Fig. 7-style molecular and functional validation panel. Until then, include the experimental design only as a proposed workflow, not as a result.

### 15.3 Recommended main figure package

Every completed figure should be exported as PDF/SVG and PNG and accompanied by a source-data table and a short caption/method note. Captions should identify the relevant inspiration (for example, “analytical layout inspired by Mathys et al., Fig. 3”) while making clear that the analysis and data are project-specific.

#### Figure 1. Focused study design and evidence hierarchy

Show:

- 276 donors and six groups;
- donor-level pseudobulk as confirmatory analysis;
- MAST as paper-comparable discovery;
- pathway, KDA, genetics/protein, and independent-cohort layers;
- clear distinction between internal consistency and replication.

#### Figure 2. Where mitochondrial change exceeds a matched non-mitochondrial baseline

Panel A: heatmap of mitochondrial DEG odds ratios or matched-null percentiles across selected fine cell type × sex/APOE contrasts.  
Panel B: forest plot for the primary cell types.  
Panel C: AD-up versus AD-down burden, with donor counts printed.

This directly answers the professor's “more profound than non-MT” question.

#### Figure 3. Donor-level interaction and pathway landscape

Use a signed dot heatmap:

- rows: prespecified mitochondrial pathways;
- columns: selected cell types and interaction contrasts;
- fill: signed pathway statistic/NES;
- size: evidence strength;
- symbol/outline: FDR significance;
- separate panels for AD-by-sex within ε2/ε3/ε4 and AD-by-APOE within females/males.

Include OXPHOS complexes, ATP synthase, translation, import/proteostasis, MIB/MICOS, mitophagy/dynamics, fatty-acid oxidation, TCA, ROS/glutathione, and iron/heme.

#### Figure 4. Mitonuclear coordination

Panel A: donor-level mtDNA ETC versus nuclear OXPHOS scatter, colored by disease and faceted by sex/APOE.  
Panel B: mitonuclear residual/imbalance with confidence intervals.  
Panel C: translation and MIB/MICOS module effects.  
Panel D: association with Braak, amyloid/tau, or cognitive resilience.

#### Figure 5. Male-ε2 and headline-effect stability

Show leave-one-donor-out and bootstrap estimates for:

- OXPHOS;
- mitonuclear imbalance;
- `Ast GRM3` `TUFM`;
- `LAMTOR5`–`ATP5IF1` module;
- `GABARAPL2`–`CHCHD2`/`PARK7` module.

#### Figure 6. Three requested layer-3 candidate subnetworks

Use contrast-specific APOE, LAMTOR5, and GABARAPL2 panels with ATP genes explicitly labeled. Provide Cytoscape TSVs and vector graphics.

#### Figure 7. Robust driver-by-context matrix

Replace the current circular plot in the main story. Display robust candidates only, separated by network and primary sex/APOE signature. Add alternative-network and matched-null stability.

#### Figure 8. Cross-validation evidence matrix

Rows: `APOE`, `LAMTOR5`, `GABARAPL2`, `SELENOW`, `FTL`, `ANKRD11`, `RPL11`, `WDR82`, `SLC11A1`, plus mediators `TUFM`, `ATP5IF1`, `CHCHD2`, `PARK7`.  
Columns: donor interaction, pathway, robust KDA, alternative network, GWAS/fine-map/QTL, RNA replication, protein support, pathology/cognition, perturbation literature, tractability.

Use a separate known-anchor label for `APOE` and distinguish “not tested” from “tested, no support.”

## 16. Candidate advancement rules

### Tier 1 now: must be tested first

- `APOE` ↔ `TUFM` in astrocytes.
- `LAMTOR5` → `ATP5IF1` in excitatory neurons.
- `GABARAPL2` → `CHCHD2`/`PARK7` in excitatory neurons.

These are Tier 1 hypotheses, not yet validated drivers.

### Tier 2: advance if the corresponding biology is significant

- `SELENOW` if neuronal redox/respiratory and tau/cognition signals replicate.
- `FTL` versus `ANKRD11` if the OPC iron/GPX4 motif survives an independent network.
- `PPARGC1B` if male-ε2 compensation survives donor stability tests.
- `WDR82` if mitonuclear discordance is significant and the mtDNA-heavy motif survives topology-matched nulls.
- `RPL11` if degree/ribosomal-hub matching and alternative networks retain it.

### Tier 3: retain as exploratory

- `SLC11A1`, `RPS15`, `TMEM147`, `BEX3`, and `HSPA1A` unless new orthogonal evidence appears.
- `RPL13` until identifier correction and rerun are complete.

### Minimum advancement criterion

A novel candidate should reach experimental planning only if it has:

1. stable donor-level support in the matching cell context;
2. robust, candidate-self-independent network support;
3. at least one orthogonal human evidence layer or independent-cohort replication;
4. a measurable predicted mediator/readout and a feasible perturbation assay.

## 17. Conditional experimental plan

If the computational gates are passed, propose:

| Candidate–mediator pair | Cell system | Perturbation | Primary readouts |
|---|---|---|---|
| `APOE` ↔ `TUFM` | APOE2/3/4-isogenic XX and XY astrocytes | APOE replacement/knockdown/rescue and reciprocal TUFM perturbation | mitochondrial translation, carbon flux, ATP synthase, respiration, mitophagy |
| `LAMTOR5` → `ATP5IF1` | APOE/sex-contextualized excitatory neurons | paired CRISPRi/CRISPRa and ATP5IF1 mediation/rescue | mTORC1 localization, ATP-synthase activity, ATP-linked respiration, proton leak, mtROS |
| `GABARAPL2` → `CHCHD2`/`PARK7` | excitatory neurons | abundance and Ser72-state perturbation; PARK7 loss/rescue | autophagosome–lysosome fusion, mitophagy, respiration, amyloid/tau-related stress |
| `FTL` versus `ANKRD11` → `FTH1`/`GPX4` | OPCs | paired perturbation under iron/lipid stress | labile iron, lipid peroxidation, GPX4, respiration, viability |

Because network edges are unsigned, use both loss- and gain-of-function, dose response, and rescue. A candidate should advance only if it moves multiple predicted targets, changes mitochondrial function, and alters an AD-relevant phenotype without nonspecific toxicity.

## 18. Decision gates and possible conclusions

### Gate 1. Do donor-level interactions support sex/APOE modification?

- **Yes:** retain sex/APOE as a central claim and focus on the significant pathways/cell types.
- **No, but consistent effects remain:** reframe sex/APOE as exploratory modifiers and make the common cell-type respiratory/mitonuclear phenotype central.
- **No and effects are donor-driven:** demote the current reversal story and do not build further KDA claims from those signatures.

### Gate 2. Is there a non-OXPHOS or mitonuclear result?

- **Mitonuclear imbalance significant:** make it the principal new biological result and use translation/MIB-MICOS/ATP/quality-control candidates to explain it.
- **A non-OXPHOS pathway significant:** focus the candidate story on that pathway, even if OXPHOS remains the common endpoint.
- **Only OXPHOS robust:** publish a narrower, well-supported respiratory-chain story; do not force fatty-acid, mitophagy, or iron conclusions.

### Gate 3. Do the highlighted drivers survive robust KDA?

- **All three survive:** retain them as distinct cell-specific candidate control systems.
- **One or two survive:** make a focused mechanism paper/figure rather than a broad driver catalog.
- **None survive:** treat the current KDA as hypothesis generation, keep the donor/pathway story, and rebuild networks before proposing perturbation.

### Gate 4. Is there orthogonal or independent support?

- **Independent RNA plus protein/genetic evidence:** candidate can be described as strongly prioritized.
- **Only same-cohort multi-omic support:** describe as orthogonally supported but not independently replicated.
- **No external support:** retain as novel, low-confidence hypothesis rather than a target.

## 19. Suggested six-week execution sequence

### Week 1: corrections and immediate figures

- freeze current inputs/outputs;
- fix `RPL13`/`MRPL13` and audit identifier collisions;
- export complete KDA test statistics;
- make APOE/LAMTOR5/GABARAPL2 subnetworks;
- replace overstatements in the presentation claim table.

### Weeks 1–2: donor-level confirmation

- run full pseudobulk production;
- add selective three-way contrasts;
- generate eligibility and donor-count tables;
- run leave-one-donor-out and bootstrap analyses for focal cell types.

### Weeks 2–3: pathways and mitonuclear analysis

- test mitochondrial versus matched non-mitochondrial burden;
- run ranked pathway tests;
- calculate mtDNA/nuclear/translation/MIB-MICOS modules;
- analyze pathology, cognition, and resilience.

### Weeks 3–4: KDA robustness

- rerun candidate-self-excluded primary directional KDA;
- correct layer selection;
- run matched nulls and focal gene-filter sensitivities;
- build/obtain at least one alternative network.

### Weeks 4–5: external and orthogonal validation

- freeze a GWAS/QTL source and run candidate integration;
- query/download permitted proteomic evidence;
- map the discovery modules to SEA-AD and/or MSBB/BLSA resources;
- prepare discovery-versus-validation comparisons.

### Week 6: synthesis

- construct the evidence matrix;
- choose the 3–5 final candidates;
- write Results/Discussion statements conditional on the decision gates;
- prepare a concise experimental-validation proposal.

The schedule assumes required Minerva, Synapse, and controlled-data access is already available. Access delays should not block P0–P2.

## 20. Required output files

Each work package should produce a tabular source behind every figure.

Suggested outputs:

```text
results/<version>/audit/analysis_freeze_manifest.tsv
results/<version>/audit/gene_identifier_corrections.tsv
results/<version>/pseudobulk/contrast_eligibility.tsv
results/<version>/pseudobulk/gene_interaction_results.tsv.gz
results/<version>/pathway/pathway_interaction_results.tsv
results/<version>/pathway/mitochondrial_vs_matched_nonmito.tsv
results/<version>/mitonuclear/donor_module_scores.tsv.gz
results/<version>/mitonuclear/mitonuclear_interaction_results.tsv
results/<version>/stability/leave_one_donor_out.tsv.gz
results/<version>/stability/donor_bootstrap_summary.tsv
results/<version>/kda/complete_candidate_by_run_pvalues.tsv.gz
results/<version>/kda/robust_driver_summary.tsv
results/<version>/networks/alternative_network_support.tsv
results/<version>/validation/genetics_qtl_evidence.tsv
results/<version>/validation/protein_evidence.tsv
results/<version>/validation/external_replication.tsv
results/<version>/validation/candidate_evidence_matrix.tsv
results/<version>/figures/<figure_name>_plotted_data.tsv
```

Every output should record the analysis version, source files, gene-set version, model/contrast ID, tested universe, donor counts, and validation status.

## 21. What not to do next

- Do not interpret separate within-stratum significance as a sex/APOE difference.
- Do not make raw DEG count or color intensity the primary statistical evidence.
- Do not describe high-similarity `(0,0)` tails as shared activation.
- Do not count pooled or `AD_both_mito` KDA runs as independent confirmation.
- Do not rank KDA candidates from the significant-only table.
- Do not call an mtDNA respiratory subunit an upstream driver solely because it appears repeatedly in KDA.
- Do not merge different broad Bayesian networks into one directed topology.
- Do not call Bayesian-network arrows activation, inhibition, or proven causality.
- Do not call ATP-synthase involvement universal across APOE calls.
- Do not prioritize `RPL13` before the identifier correction.
- Do not build 54 fine-cell MEGENA networks unless donor-level stability and gene coverage are adequate.
- Do not call multi-region ROSMAP or overlapping ROSMAP proteomics independent cohort replication.
- Do not continue expanding the candidate list until the first three candidates pass or fail the stated gates.

## 22. Immediate next actions

The first five concrete actions are:

1. Correct `RPL13`/`MRPL13` and generate a presentation claim-audit table.
2. Produce the requested APOE, LAMTOR5, and GABARAPL2 layer-3 subnetwork figures with exact contrast-specific DEG coloring and ATP labels.
3. Run the existing full pseudobulk pipeline and direct interaction contrasts on Minerva.
4. Run the prespecified pathway and mitonuclear-coordination analysis in the focal cell systems.
5. Decide at Gate 1 whether sex/APOE remains the headline before spending time on broad genetics/network integration.

## 23. Source map

Professor requirements and interpretation:

- [August 4 meeting notes](../email_notes/notes_08042026.txt)
- [August 4 subnetwork request](../email_notes/email_08042026.txt)
- [July 25 project definition](../email_notes/email_07252026.txt)
- [July 28 deeper-mining/validation notes](../email_notes/notes_07282026.txt)
- [Circular-ranking analysis](../email_notes/email_08042026_circular_figure_sort_order.md)

Current results:

- [Most recent DEG–KDA presentation](<../presentations/DEG-KDA Final Results v2.pdf>)
- [Joint Phase 11–12 discussion](../analysis/phase11_phase12_joint_mitochondrial_discussion.md)
- [Three selected mitochondrial connections](../analysis/phase11_phase12_selected_mitochondrial_connections.md)
- [Current high-priority sections](../analysis/section_priority.md)
- [Current KDA results](../../results/minerva_production/12_kda/kda_results.tsv.gz)
- [Current KDA run manifest](../../results/minerva_production/12_kda/kda_run_manifest.tsv)

Related studies:

- [Mathys single-cell atlas](<../related_papers/mathys single-cell atlas reveals correlates.pdf>)
- [Yu sex/APOE study](../related_papers/yu_paper/Yu_sex_apoe.pdf)
- [Yu methods summary](../related_papers/yu_paper/Yu_sex_apoe_method.md)
- [Wang multiscale/protein-network study](../related_papers/wang_multiscale_modeling.pdf)

External validation resources to freeze before use:

- [SEA-AD](https://sea-ad.org/) and [SEA-AD analysis code](https://github.com/AllenInstitute/SEA-AD_2024)
- [NIAGADS Alzheimer's Genomics Database](https://www.niagads.org/genomics/)
- [Agora AD target-evidence portal](https://agora.adknowledgeportal.org/)
- [AD Knowledge Portal documentation](https://help.adknowledgeportal.org/)
