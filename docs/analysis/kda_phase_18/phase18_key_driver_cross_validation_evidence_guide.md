# Phase 18 DEG/KDA findings: general cross-validation plan

**Date:** 2026-08-16  
**Status:** Recommended validation framework  
**Primary question:** How should the DEG and KDA findings be cross-validated, and where does STRING-db fit within the larger validation strategy?

## A. Study intent summary

### Biological objective

The project has identified cell-type- and sex/APOE-associated mitochondrial DEG programs and used directed Bayesian networks to nominate key drivers whose neighborhoods are enriched for those mitochondrial genes.

The next objective is to determine which findings are:

- internally robust;
- reproducible in independent human data;
- conserved in a relevant APOE model;
- supported by human genetic variation;
- supported at the protein level;
- consistent with prior protein-network knowledge; and
- capable of producing the predicted phenotype when experimentally perturbed.

The professor's notes ask for a stronger case for the top key drivers through genetic variation in AD patients, other data, and “protein geomics.” The last phrase is most naturally interpreted as **proteomics** or **proteogenomics** rather than STRING alone.

### What “cross-validation” means here

This is not ordinary machine-learning k-fold cross-validation. It is a combination of:

1. **robustness analysis:** does the result survive alternative analytical choices?
2. **external replication:** does the result recur in independent biological samples?
3. **orthogonal validation:** do genetics, proteins, spatial measurements, or functional experiments support it?

The Phase 08 DEG and Phase 18 KDA results were derived from the same study. Agreement between them is useful internal consistency, but it is not independent validation. Likewise, multiple KDA runs using the same broad Bayesian network are repeated contexts, not fully independent network replications.

### Primary validation unit

Use one row per:

```text
key driver × broad cell-type network
```

Retain the supporting run-level context:

```text
kda_run_id
fine_cell_type
sex
APOE group
signature_direction
predicted mitochondrial targets
```

A gene selected in astrocytes and excitatory neurons therefore has two validation units rather than one pooled result.

### Scope assumptions

- The current Phase 18 candidate list and ranking are frozen before external validation.
- External sample availability and wet-lab capacity have not been assumed.
- Any public or collaborator-provided data must be audited before use.
- The immediate goal is candidate prioritization and mechanism validation, not clinical biomarker deployment.

## B. Best-fit study pattern

### Dominant pattern: translational target discovery

The best-fit pattern is **translational target discovery** because the project is moving from network-derived candidates toward a smaller set with defensible human, protein, and functional evidence.

The intended inference is:

```text
cell-type mitochondrial disease program
    →
network-associated candidate driver
    →
independent multi-layer support
    →
prioritized experimental target
```

### Supporting pattern: key-cell/key-state prioritization

A secondary pattern is **key-cell/key-state prioritization**. The same gene may be convincing in one cell type but not another. External replication must therefore preserve cell type and should not collapse all gene occurrences into a single gene-level conclusion.

Trajectory, RNA velocity, and cell-cell communication are not default validation modules for the present question. They should be added only if a specific candidate mechanism requires them.

## C. Four workload configurations

| Configuration | Goal | Required evidence layers | Validation strength | Main deliverable | Main limitation |
|---|---|---|---|---|---|
| **Lite** | Rapidly identify fragile versus credible candidates | Internal robustness, targeted literature review, small STRING pilot | Within-study plus prior-knowledge support | Short evidence matrix for Wave 1 genes | Little independent disease replication |
| **Standard** | Add one genuine external layer | Lite + independent human transcriptomic or proteomic replication | Within-study + one external/orthogonal layer | Candidate ranking with one replicated result | Causality remains untested |
| **Advanced** | Build a strong computational validation package | Standard + cross-species replication, genetics, proteogenomics, alternative-network/null analyses | Cross-dataset + multiple orthogonal layers | Publication-oriented validation atlas | Depends on compatible external data and metadata |
| **Publication+** | Test mechanism directly | Advanced + perturbation, rescue, and pathway/mitochondrial phenotyping | Multi-layer plus functional evidence | Mechanistic candidate paper/package | Requires substantial experimental resources |

The configurations are nested:

```text
Lite ⊂ Standard ⊂ Advanced ⊂ Publication+
```

Higher configurations extend rather than replace the lower-level analyses.

## D. Recommended primary plan

### Recommendation: Advanced computational validation, followed by selective Publication+ experiments

The best fit is the **Advanced** configuration because:

- Phase 18 already contains a developed discovery and prioritization framework;
- the professor specifically requested stronger genetic and protein evidence;
- the project is considering moving toward experiments;
- the candidate list contains important topology-bias risks, especially ribosomal and respiratory-chain genes; and
- a single STRING figure would not adequately answer whether the findings replicate in AD.

The immediate minimum executable milestone is the **Standard** configuration: perform rigorous internal robustness tests and add one verified independent human transcriptomic or proteomic layer.

Publication+ should be reserved for a small set of candidates selected after the computational evidence matrix is complete. It is not necessary to perturb all 25 genes.

### Initial candidate panel

Start with a deliberately diverse panel:

| Candidate | Main context | Why it is informative for validation |
|---|---|---|
| APOE | Astrocytes | Established AD positive control; validates the specific mitochondrial neighborhood rather than APOE itself |
| SELENOW | Excitatory neurons | Strong KDA signal with relevant external mechanistic precedent |
| LAMTOR5 | Excitatory and inhibitory neurons | Mechanistically plausible lysosome–mTOR–mitochondria candidate with limited direct AD evidence |
| RPL11 | Astrocytes and excitatory neurons | Broad recurrence but vulnerable to ribosomal/hub bias |
| FTL | OPCs | Exploratory iron/ferroptosis candidate requiring cell-type localization |
| ANKRD11 | OPCs | Exploratory chromatin candidate requiring independent subtype replication |

This panel includes positive-control, externally reinforced, under-studied, bias-sensitive, and cell-type-specific cases. It will reveal whether the validation framework behaves sensibly before extension to all 47 displayed gene × network contexts.

## E. Data strategy and example resource directions

### Discovery data to freeze

Use the current validated Phase 18 outputs without changing the candidate-selection rule after viewing external evidence:

- [`call_key_driver_returns.tsv`](../../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv)
- the [Phase 18 selection process](../../phase_18_key_driver_selection/key_driver_selection_process.md)
- the [initial gene-by-gene interpretation](phase18_key_driver_gene_by_gene_initial_analysis.md)

For every candidate-context unit, freeze:

- key driver and driver class;
- broad network and supporting fine cell types;
- sex/APOE group and mitochondrial direction;
- KDA layer and directed neighborhood;
- exact mitochondrial query and overlap genes;
- tested-gene background;
- aggregate and run-level statistics; and
- stability/sensitivity results.

### External human transcriptomic direction

A suitable external human validation source would ideally contain:

- human AD and control brain samples;
- donor identifiers and true biological replicates;
- a comparable brain region;
- single-nucleus/single-cell counts or donor-level pseudobulk data;
- cell types that can be mapped defensibly to the discovery labels;
- sex, diagnosis, APOE genotype, age, batch, and other relevant covariates; and
- enough donors per contrast to estimate effects rather than merely visualize them.

Reference directions may include an independent human AD single-cell/single-nucleus cohort or a verified disease-focused atlas. Suitability must be checked; repository presence alone does not establish that the required groups or metadata exist.

### Cross-species/model direction

The professor has indicated that APOE knock-in mouse single-cell data may be provided. Before analysis, verify:

- exact APOE genotype or targeted-replacement design;
- disease model and control design;
- age, sex, brain region, and tissue processing;
- sample-level replicate structure;
- availability of raw counts or valid normalized data;
- cell-type annotation quality; and
- one-to-one human–mouse ortholog coverage for the frozen targets.

Do not assume the dataset is suitable until these details are confirmed.

### Genetics directions

Reference resources include:

- [NIAGADS Alzheimer's GenomicsDB](https://www.niagads.org/genomics/) for AD-focused GWAS summaries and annotated variants;
- [NIAGADS/ADSP](https://www.niagads.org/) for sequencing resources and qualified-access data; and
- the [NHGRI–EBI GWAS Catalog](https://www.ebi.ac.uk/gwas/) for curated associations and available summary statistics.

Required information includes ancestry, phenotype, sample size, genome build, effect alleles, summary statistics, fine-mapping information, and multiple-testing status.

### Protein and proteogenomic directions

[Agora](https://agora.adknowledgeportal.org/about) is a reference candidate for harmonized AD transcriptomic, proteomic, and metabolomic target evidence. The [AD Knowledge Portal](https://adknowledgeportal.synapse.org/) is a reference direction for underlying AMP-AD and related data.

Before selecting a protein dataset, verify:

- cohort independence from discovery data;
- brain region and disease definition;
- protein platform and identifier mapping;
- peptide or probe reliability;
- case/control and covariate structure;
- cell-type or spatial resolution;
- protein missingness and detectability; and
- whether individual-level or summary-level data are available.

### Minimum metadata inventory

Create a data-suitability table containing:

```text
resource_name
resource_type
species
tissue_or_brain_region
modality
disease_groups
APOE_groups
sex_available
donor_or_animal_id_available
replicate_structure
raw_counts_or_valid_input
candidate_gene_coverage
target_module_coverage
access_status
main_limitation
suitability_decision
```

## F. Core analysis modules and method choices

| Module | Purpose | Use level | Preferred method | Important constraint |
|---|---|---|---|---|
| Freeze candidate-context hypotheses | Prevent validation-driven reselection | Necessary | Versioned manifest | Must precede external queries |
| Internal KDA robustness | Test sensitivity to network and threshold choices | Necessary | Leave-one-fine-cell-type-out, alternative thresholds, matched nulls | Runs sharing a broad network are not independent |
| Candidate DEG replication | Test whether candidate expression changes externally | Recommended | Donor-level pseudobulk; DESeq2 for counts, limma for normalized non-count data | Candidate need not be a DEG for KDA to be valid |
| Target-module replication | Test the actual KDA-predicted mitochondrial program | Necessary | Frozen module score, ranked enrichment, effect concordance | Use all measurable frozen targets |
| Formal sex/APOE inference | Test interaction rather than subgroup significance | Recommended | Donor-level disease × sex/APOE models | Do not treat nuclei as replicates |
| Cross-species replication | Test conservation in APOE models | Recommended | One-to-one ortholog mapping and matched cell-type module tests | Model-stage and species differences limit interpretation |
| Common-variant genetics | Connect candidate to AD risk loci | Recommended | GWAS lookup, fine mapping, variant-to-gene evidence | Nearest gene is not necessarily causal |
| Rare-variant genetics | Test burden of damaging variation | Advanced | Published/qualified-access burden analyses | A variant observed in cases is not association evidence |
| eQTL/sQTL colocalization | Test shared AD and regulatory signals | Advanced | Fine-mapping-aware colocalization where possible | Requires compatible ancestry and adequate locus signal |
| Protein-abundance replication | Test protein-level disease association | Recommended | Covariate-adjusted differential abundance and meta-analysis | Bulk signals may reflect cell composition |
| pQTL–GWAS colocalization | Connect genetically regulated protein abundance to AD risk | Advanced | Colocalization with sensitivity analysis | Shared signal is not proof of mediation |
| STRING protein network | Test prior protein association among driver and targets | Supporting | Physical and functional input-only networks | Not AD-, cell-type-, or direction-specific |
| Perturbation/rescue | Test functional-driver behavior | Publication+ | Graded CRISPRi/a, orthogonal reagent, rescue | Avoid interpreting generalized toxicity as specificity |
| Evidence integration | Rank candidates transparently | Necessary | Evidence matrix and tiers | Avoid one opaque database-count score |

### Statistical principles

1. Define primary hypotheses, contrasts, and success criteria before looking at validation results.
2. Treat donors, animals, independent differentiations, or clones—not cells or wells—as biological units.
3. Report effect sizes and confidence intervals with P values.
4. Apply Benjamini–Hochberg FDR within clearly defined test families.
5. Report missingness and measurement coverage; do not silently remove unavailable targets.
6. Use sensitivity analysis rather than post-hoc observed power for completed studies.
7. A nonsignificant result is inconclusive unless the analysis has adequate precision or an equivalence/Bayesian analysis supports a negligible effect.
8. Keep confirmatory and exploratory analyses separate.

## G. Seven validation evidence layers

### Evidence 1 — internal statistical and network robustness

#### Question

Does the finding survive reasonable changes in analysis, and is it stronger than expected for genes with similar expression and network topology?

#### Analyses

For each `key_driver × broad_network` unit:

1. retain the existing Phase 18 gates:

   ```text
   coverage_fraction >= 0.80
   conservative_support_count >= 1
   aggregate_acat_q <= 0.05
   ```

2. summarize supporting fine cell types, sex/APOE groups, and directions without calling them independent replicates;
3. perform leave-one-fine-cell-type-out analyses;
4. repeat KDA under defensible edge-confidence or network-pruning settings;
5. test sensitivity to mitochondrial read fraction, RNA quality, nucleus quality, inferred mitochondrial mass, and mtDNA copy number where available;
6. compare the selected driver with genes matched on expression, Bayesian-network degree, neighborhood size, and functional class; and
7. use special ribosomal-gene and respiratory-chain matched nulls.

#### Strong support

- aggregate evidence remains significant;
- support comes from more than one fine cell type;
- the candidate survives leave-one-out analyses;
- ranking is stable under reasonable network choices; and
- enrichment exceeds matched null genes.

#### Limitations

This layer validates robustness, not external biological replication. A tiny ACAT q value does not make reused networks or overlapping contexts independent.

### Evidence 2 — independent human transcriptomic replication

#### Question

Does an independent human cohort reproduce the candidate or, more importantly, its predicted mitochondrial target module in the matched cell type?

#### Hypotheses

Freeze two separate hypotheses:

1. **candidate-expression hypothesis:** the driver itself changes in the predicted disease context;
2. **target-module hypothesis:** the frozen KDA target set changes coherently even if the driver is not a DEG.

The second hypothesis is more faithful to KDA because an upstream regulator need not change in abundance.

#### Analysis

1. audit sample metadata and independence;
2. map external cell types without forcing the original labels;
3. aggregate counts at the donor × cell-type level;
4. use DESeq2 for count pseudobulk or limma for non-count normalized data;
5. include diagnosis and defensible covariates such as age, sex, brain region, postmortem interval, ancestry, and batch;
6. fit formal disease × sex and disease × APOE terms for interaction claims;
7. test candidate log fold change, standard error, confidence interval, and FDR;
8. test the complete frozen target module using ranked enrichment or a prespecified module score;
9. calculate gene-level directional concordance and discovery-versus-replication effect correlation; and
10. meta-analyze only compatible cohorts, reporting heterogeneity.

#### Strong support

- the matched cell type reproduces the target-module direction;
- the result uses donor-level replication;
- a substantial fraction of targets agree directionally;
- the effect is not driven by one donor or batch; and
- the finding survives multiple-testing correction or a prespecified focused test.

#### Limitations

- Reusing the discovery cohort is not external replication.
- Counting nuclei as independent replicates creates pseudoreplication.
- Failure of the candidate itself to be a DEG does not automatically invalidate KDA.
- Subgroup significance in one APOE group and nonsignificance in another is not evidence of interaction.

### Evidence 3 — cross-species or APOE-model replication

#### Question

Does the candidate-target program recur in a relevant APOE knock-in or AD model in the corresponding cell type?

#### Analysis

1. verify animal-level replicates, genotype, disease model, age, sex, region, and batch;
2. map human genes to reliable one-to-one mouse orthologs;
3. report targets without one-to-one orthologs separately;
4. match cell types conservatively using marker programs and biological identity;
5. use animal-level pseudobulk rather than cells as replicates;
6. fit the genotype/disease contrast that most closely matches the human hypothesis;
7. test candidate expression and frozen orthologous target-module activity;
8. report directional concordance, effect correlation, and module statistics; and
9. distinguish exact replication from pathway-level conservation.

#### Strong support

- the orthologous target module changes in a matched cell type;
- the result occurs in multiple animals rather than one library;
- direction is coherent with the human result; and
- the model design is biologically relevant to the claimed APOE mechanism.

#### Limitations

Cross-species evidence supports conservation, not direct replication of human AD. Discordance may reflect species, age, disease stage, region, model biology, or ortholog coverage.

### Evidence 4 — human genetic support

#### Question

Is inherited variation affecting the candidate plausibly associated with AD risk, protection, age at onset, cognition, or an AD-related phenotype?

#### Common-variant evidence

For each candidate, record:

- AD GWAS study and accession;
- ancestry and sample size;
- lead variant, effect allele, effect size, and P value;
- whether the candidate is merely nearby or supported by fine mapping;
- credible-set membership and variant posterior probability where available;
- relevant brain or cell-type regulatory annotations; and
- whether eQTL/sQTL colocalization nominates the same gene.

#### Rare-variant evidence

Look for gene-burden, SKAT/SKAT-O, loss-of-function, damaging-missense, or family-segregation evidence. Record the variant mask, frequency cutoff, ancestry, case/control definition, multiple-testing correction, and replication status.

Do not write that a gene “tends to be mutated in AD” simply because variants were observed in affected people. Nearly every adequately sequenced gene contains variants. The meaningful evidence is statistical enrichment, segregation, or replicated association relative to controls.

#### Evidence grading

- **Strong:** fine-mapped coding evidence, replicated rare-variant burden, or well-supported colocalization with a relevant molecular QTL.
- **Moderate:** an AD locus plus several convergent functional mappings to the candidate.
- **Weak:** nearest-gene assignment or an uncorrected nominal association.
- **No evidence found:** no convincing result in the examined resources; this is not proof that the gene has no role.

#### Mitochondrial genes

Standard nuclear GWAS is insufficient for mtDNA-encoded candidates. Consider mtDNA variants, heteroplasmy, copy number, haplogroup, tissue-specific selection, and nuclear regulators of mitochondrial expression or complex assembly.

### Evidence 5 — proteomic and proteogenomic support

#### Question

Is the candidate protein, predicted target-protein module, or relevant protein complex altered in human AD, and is any AD genetic signal shared with protein abundance?

#### Protein-abundance analysis

For each cohort and protein:

1. confirm stable protein identifiers and peptide/probe specificity;
2. quantify missingness and detection coverage;
3. model AD versus control with study-appropriate covariates;
4. report effect size, standard error, confidence interval, raw P value, and FDR;
5. record brain region, assay platform, and cell-type resolution;
6. test replication across independent cohorts;
7. test the frozen target-protein module when individual proteins are incompletely measured; and
8. separate individual-protein evidence from protein-coexpression-module evidence.

#### Protein-complex and functional measures

For structural mitochondrial candidates, protein abundance alone is incomplete. Useful orthogonal measures include:

- respiratory-complex assembly;
- supercomplex composition;
- complex enzymatic activity;
- mitonuclear subunit stoichiometry;
- mitochondrial mass;
- mtDNA copy number and heteroplasmy; and
- oxygen-consumption or membrane-potential measures.

For lysosomal candidates, consider protein localization, lysosomal pH, V-ATPase assembly, autophagic flux, and mitophagy.

#### pQTL–AD-GWAS colocalization

When a suitable cis-pQTL exists:

1. harmonize genome build, alleles, ancestry, locus, and variant set;
2. confirm that both AD GWAS and pQTL signals have adequate regional evidence;
3. account for multiple independent signals through fine mapping or conditional analysis;
4. run colocalization and report all hypotheses, not only the shared-signal posterior;
5. perform prior and locus sensitivity analyses;
6. check whether coding variants alter assay binding rather than protein abundance; and
7. report the direction from allele to protein abundance to AD risk.

A high shared-signal posterior supports a shared variant. It does not by itself prove that the protein mediates AD risk or identify a safe therapeutic direction.

#### Project-specific cautions

- RPL11/RPL15 vascular protein evidence does not automatically validate an astrocyte or neuronal mechanism.
- Bulk-tissue protein changes may reflect altered cell composition.
- Ribosomal proteins may validate a translation-stress module more strongly than separate causal genes.
- Hydrophobic mtDNA-encoded membrane proteins may be poorly measured by standard proteomics.

### Evidence 6 — prior protein-network support, including STRING-db

#### Question

Are the selected driver and its exact KDA-predicted mitochondrial targets connected by external experimental, curated, or functional protein evidence?

STRING is a **supporting orthogonal approach**, not the overall validation strategy.

#### Should DEG and KDA genes be submitted together?

Yes, but only as matched, prespecified sets:

```text
one selected key driver
    +
the mitochondrial DEG targets in that driver's KDA neighborhood
    +
the original biological-context labels
```

Do not submit all DEGs, every selected driver, and all Bayesian-network nodes as one primary analysis. That would mix cell types and directions and generate predictable ribosomal/OXPHOS connectivity.

#### Primary STRING analysis

For each driver-context set:

```text
organism: Homo sapiens (9606)
network type: physical
minimum score: high confidence, approximately 0.700
added first-shell proteins: 0
added second-shell proteins: 0
primary edge support: experiments and curated databases
```

Record identifier mapping, driver–target edges, experimental/database channel scores, observed and expected edges, PPI-enrichment P value, and pathway enrichment.

Run a second **functional network** analysis for broader pathway concordance. Coexpression- or text-mining-only connections are exploratory because they are not strongly independent of transcriptomic discovery or literature attention.

#### Controls

Compare each driver-target set with:

1. matched control drivers from the same Bayesian network, matched on expression, Bayesian degree, neighborhood size, STRING degree, and functional class; and
2. matched mitochondrial target sets, matched on expression, detectability, STRING degree, and functional class.

For a metric where larger means stronger support:

```text
empirical_p =
    (1 + number of null values >= observed value)
    /
    (1 + number of null permutations)
```

Correct across the family of driver-context tests.

#### Interpretation

- Driver-to-target experimental/database edges exceeding matched nulls provide protein-network support.
- A connected target module with an isolated driver supports the DEG module, not the driver.
- Ribosomal or respiratory-complex connectivity supports module membership but may not identify a unique upstream regulator.
- No STRING edge means no current database support, not proof that the relationship is false.
- STRING does not validate Bayesian edge direction, AD specificity, or cell-type specificity.

See the official STRING descriptions of [network types and evidence channels](https://string-db.org/help/scores/) and the [STRING API](https://string-db.org/help/api/).

### Evidence 7 — perturbation, rescue, and functional validation

#### Question

Does changing the candidate alter the frozen KDA-predicted mitochondrial target module and the relevant cellular phenotype?

This is the strongest evidence for a functional-driver claim.

#### Experimental principles

1. match the cell model to the KDA context;
2. use APOE-isogenic backgrounds when the hypothesis is APOE dependent;
3. represent biological sex or sex-chromosome background if a sex interaction is claimed;
4. use graded CRISPRi/CRISPRa or titratable perturbation for essential ribosomal/OXPHOS genes;
5. use at least two independent reagents;
6. include non-targeting, pathway-positive, and toxicity controls;
7. freeze the target list before the experiment;
8. use independent donors, clones, or differentiations as biological replicates;
9. measure early time points before generalized stress dominates; and
10. include an sgRNA-resistant or mechanistically appropriate rescue.

#### Primary endpoints

- candidate RNA and protein perturbation;
- frozen target-module RNA and protein response;
- directional concordance with the predicted KDA relationship;
- pathway-proximal readouts;
- mitochondrial respiration, membrane potential, or other relevant functions;
- viability, global translation, integrated stress, cell cycle, and mitochondrial-mass controls; and
- rescue of both module and phenotype.

#### Candidate-specific examples

| Candidate/class | Key readouts |
|---|---|
| RPL11/ribosomal candidates | Nascent translation, nucleolar stress, MDM2–p53, integrated stress, target selectivity |
| LAMTOR5 | Lysosomal pH, Ragulator/mTORC1 localization, phospho-S6K/4EBP1, mitophagy |
| APOE | Cholesterol distribution, lipid droplets, substrate use, mitophagy, respiration |
| SELENOW | ROS, glutathione/redox state, proteasome function, tau clearance, respiration |
| FTL | Labile iron, ferritin, lipid peroxidation, ferroptosis sensitivity, respiration |
| ANKRD11 | Chromatin accessibility/occupancy, OPC differentiation, myelination, respiration |
| MT/OXPHOS subunits | Complex assembly/activity, supercomplexes, membrane potential, mtDNA quantity, ROS |

#### Functional-driver success criteria

A persuasive result should show:

1. successful candidate perturbation;
2. reproducible change in the frozen target module;
3. the expected pathway/mitochondrial phenotype;
4. effects before or without generalized toxicity;
5. replication with an independent reagent; and
6. reversal by rescue.

If perturbation only causes global translation arrest or respiratory collapse, the result supports essential module membership rather than selective upstream regulation.

## H. Step-by-step workflow

> **Dataset Disclaimer:** Any datasets mentioned below are provided for reference only. Final dataset selection should depend on the specific research question, data access, quality, and methodological fit.

### Step 1 — freeze the discovery hypotheses

Create one manifest row per gene × broad network, with supporting runs and exact targets. Do not modify the candidate list after viewing Agora, STRING, genetics, or external replication results.

### Step 2 — build the validation matrix shell

Create columns for all seven evidence layers and explicit values for:

```text
support
contradiction
inconclusive
not measured
not evaluated
```

Absence of measurement must not be treated as negative evidence.

### Step 3 — complete internal robustness tests

Perform leave-one-fine-cell-type-out, alternative-network/threshold sensitivity, technical-covariate sensitivity, and matched-null tests. Demote candidates whose signal depends on one subtype or network feature.

### Step 4 — identify and audit external human transcriptomic candidates

Search only for data with compatible tissue, diagnosis, cell types, donor structure, and metadata. Complete the suitability inventory before downloading or analyzing a candidate resource.

### Step 5 — perform donor-level external replication

Test candidate expression and the frozen target module in matched cell types. Use formal disease × sex/APOE models where relevant and report effect sizes, confidence intervals, directional concordance, and FDR.

### Step 6 — analyze the collaborator-provided APOE model if suitable

After verifying its design and metadata, map one-to-one orthologs and test the corresponding cell-type target modules using animals as replicates.

### Step 7 — compile human genetic evidence

Use verified AD GWAS and sequencing resources. Separate nearest-gene, fine-mapped, rare-burden, and colocalized regulatory evidence. Record study accessions and ancestry.

### Step 8 — compile and analyze protein evidence

Use verified independent human proteomic evidence, test protein abundance and module effects, evaluate cellular localization, and perform pQTL–AD-GWAS colocalization where data are adequate.

### Step 9 — perform STRING as one protein-network layer

Run input-only physical and functional networks for each driver plus its exact KDA targets. Export mapping, edges, evidence channels, PPI enrichment, matched-null results, version, access date, and SVG.

### Step 10 — integrate evidence without double counting

Keep internal DEG/KDA evidence, external expression, genetics, proteins, STRING, and experiments in separate columns. Do not count multiple databases that reuse the same underlying study as independent replications.

### Step 11 — select experimental candidates

Advance a small set representing:

- one established positive control;
- one externally reinforced candidate;
- one novel mechanistic candidate; and
- optionally one bias-sensitive module-anchor candidate.

### Step 12 — perform graded perturbation and rescue

Test the frozen target module before broad exploratory phenotyping. Require orthogonal reagents, toxicity controls, and rescue before claiming functional-driver status.

### Step 13 — update conclusions and candidate tiers

State which layer supports each claim and preserve contradictory or inconclusive results. If individual-gene support fails but the module replicates, shift the conclusion to a system-level finding rather than discarding the entire project.

## I. Validation evidence hierarchy

| Evidence level | What it establishes | Example in this project | Maximum defensible claim |
|---|---|---|---|
| 1. Within-study consistency | Signal recurs under the current contrasts | Candidate is a DEG and/or recurrent KDA result | Internally supported association |
| 2. Analytical robustness | Signal is not dependent on one threshold or topology feature | Leave-one-out and matched-null survival | Robust network-associated candidate |
| 3. Cross-dataset replication | Similar signal occurs in independent samples | Human donor-level target-module replication | Replicated cell-type disease program |
| 4. Cross-species/model support | Program is conserved in a relevant model | APOE knock-in target-module concordance | Conserved model-supported mechanism |
| 5. Orthogonal human evidence | Genetics or protein data support the candidate | Fine mapping, colocalization, protein replication | Human multi-omic support |
| 6. Prior protein-network support | Known protein evidence connects driver and targets | STRING experimental/database edges | Protein-network concordance |
| 7. Perturbation and rescue | Intervention changes the target module and phenotype | CRISPRi/a plus rescue | Functional-driver evidence |

Evidence levels are not interchangeable. STRING can strengthen Level 6 but cannot substitute for independent human replication, disease genetics, or perturbation.

### Suggested integrated tiers

- **Tier A — externally reinforced functional candidate:** robust KDA, at least one independent disease-specific human/model layer, and perturbation/rescue or strong convergent genetics/proteomics.
- **Tier B — multi-omic mechanistic candidate:** robust KDA plus independent transcriptomic, genetic, or protein support, but no decisive functional test.
- **Tier C — robust discovery candidate:** survives internal robustness but lacks convincing external support.
- **Tier D — module sentinel:** strongly identifies ribosomal, lysosomal, iron, transport, or OXPHOS biology, but individual-driver causality is not established.
- **Tier E — fragile/exploratory:** depends on one context or fails key robustness checks.

Do not calculate one opaque total score unless weights and dependencies are prespecified. A transparent evidence matrix is preferable.

## J. Figure and deliverable plan

### Main figures

1. **Validation workflow:** discovery → seven evidence layers → integrated candidate tiers.
2. **Internal robustness atlas:** recurrence, ACAT evidence, stability, and matched-null results.
3. **External human replication:** candidate and target-module effect sizes with confidence intervals by cell type/cohort.
4. **Cross-species comparison:** human-versus-model target concordance and cell-type module effects.
5. **Genetic/proteomic evidence atlas:** fine mapping, rare variants, colocalization, protein abundance, and complex/activity support.
6. **KDA–STRING paired networks:** original directed Bayesian neighborhood beside input-only STRING protein evidence.
7. **Integrated evidence heatmap:** one row per driver × broad network, one column per evidence layer.
8. **Perturbation/rescue figure:** frozen module, pathway-proximal phenotype, mitochondrial function, toxicity controls, and rescue.

### Minimal deliverables

```text
phase18_validation_candidate_manifest.tsv
phase18_internal_robustness.tsv
phase18_external_human_replication.tsv
phase18_cross_species_replication.tsv
phase18_genetic_evidence.tsv
phase18_proteomic_evidence.tsv
phase18_pqtl_gwas_colocalization.tsv
phase18_string_edges.tsv
phase18_string_summary.tsv
phase18_perturbation_results.tsv
phase18_integrated_validation_matrix.tsv
```

Every external-evidence row should include the source, version/accession, access date, population/tissue, analysis method, measurement status, and limitation.

## K. Verified reference layer

### Project sources

- [Phase 18 key-driver selection process](../../phase_18_key_driver_selection/key_driver_selection_process.md)
- [Phase 18 initial gene-by-gene interpretation](phase18_key_driver_gene_by_gene_initial_analysis.md)
- [Professor's notes after the 2026-08-12 presentation](../../email_notes/notes_after_08122026_presentation.txt)

### Official resources and method support

- STRING. [Network types and evidence channels](https://string-db.org/help/scores/).
- STRING. [API documentation](https://string-db.org/help/api/).
- Agora. [About the AD target-evidence platform](https://agora.adknowledgeportal.org/about).
- AD Knowledge Portal. [AD data and resources](https://adknowledgeportal.synapse.org/).
- NIAGADS. [Alzheimer's GenomicsDB](https://www.niagads.org/genomics/).
- NIAGADS. [AD genetics and genomics repository](https://www.niagads.org/).
- NHGRI–EBI GWAS Catalog. [Search and data access](https://www.ebi.ac.uk/gwas/).
- NHGRI–EBI GWAS Catalog. [Summary-statistics documentation](https://www.ebi.ac.uk/gwas/docs/methods/summary-statistics).
- Giambartolomei C, et al. Bayesian test for colocalisation between pairs of genetic association studies using summary statistics. *PLoS Genetics*. 2014. [doi:10.1371/journal.pgen.1004383](https://doi.org/10.1371/journal.pgen.1004383).

Formal disease- and gene-specific references already reviewed for the current candidates are listed in the [Phase 18 initial gene-by-gene report](phase18_key_driver_gene_by_gene_initial_analysis.md). Any new candidate-specific literature should be directly verified before it is added to the evidence matrix.

## L. Self-critical risk review

### Strongest part of the plan

The plan separates the exact KDA-predicted target module from the candidate's own DEG status and tests that frozen hypothesis across independent modalities. This directly addresses what KDA claims.

### Most assumption-dependent part

The directed Bayesian-network interpretation remains assumption-dependent. Repeated runs within a broad cell type reuse the same network, and a topological key driver may be a module anchor rather than a molecular regulator.

### Most likely false-positive source

High expression, large neighborhoods, STRING degree, and functional-class structure can favor ribosomal and respiratory-chain genes. Expression-, degree-, neighborhood-, detectability-, and class-matched nulls are essential.

### Easiest result to overinterpret

The easiest results to overinterpret are:

- sex/APOE counts without a formal interaction model;
- a significant STRING PPI-enrichment P value;
- known OXPHOS complex membership;
- a protein change in bulk tissue without cell-type localization; and
- a variant near a gene without fine mapping or colocalization.

### Likely reviewer criticisms

- discovery and validation use overlapping samples;
- broad-network reuse inflates perceived recurrence;
- external cell types or brain regions are poorly matched;
- nuclei are treated as replicates;
- candidate prioritization is influenced by post hoc literature;
- ribosomal/OXPHOS hubs are overinterpreted;
- STRING is presented as disease-specific validation;
- external datasets lack power or key metadata; or
- causal language is used without perturbation and rescue.

### Fallback if individual candidates do not validate

If individual-gene evidence collapses but target modules replicate, retain the system-level conclusions:

- ribosomal stress/translation;
- lysosome–mTOR/mitophagy;
- iron handling and ferroptosis;
- intracellular transport; and
- mitonuclear respiratory remodeling.

The defensible fallback is that Phase 18 identifies coherent cell-type-specific systems and nominates genes for testing—not that all selected genes are independent causal drivers.

## Final recommendation

Cross-validation should proceed as a ladder:

```text
freeze DEG/KDA hypotheses
    →
test internal robustness
    →
replicate frozen target modules in independent human data
    →
test conservation in the APOE model
    →
add human genetics and proteomics/proteogenomics
    →
use STRING as one protein-network support layer
    →
perturb and rescue only the best-supported candidates
```

STRING-db is useful, but it should not organize or substitute for the general validation plan. For STRING specifically, submit each selected driver with its exact context-matched KDA-overlap mitochondrial DEGs; do not pool all DEGs and all network genes. The strongest candidates will be those supported by several independent layers, especially external human replication and functional perturbation/rescue.

