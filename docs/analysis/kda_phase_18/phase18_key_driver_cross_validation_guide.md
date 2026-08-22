# Publication validation plan for the Phase 18 DEG/KDA findings

**Date:** 2026-08-16  
**Goal:** Produce publication-ready evidence for a small set of cell-type-specific mitochondrial key-driver findings.

**Scope:** This document specifies what must be done, how to do it, the required outputs, and the evidence needed for each claim.

## 1. Publication objective and claim limits

The paper should not claim that all 25 displayed genes are causal AD drivers. The defensible publication strategy is to:

1. show that the mitochondrial DEG/KDA results are analytically robust;
2. select a small, biologically diverse candidate panel;
3. reproduce the candidate-target programs in independent data;
4. add human genetic, protein, and protein-network evidence;
5. rank candidates using a transparent evidence matrix; and
6. experimentally perturb the strongest candidates if the manuscript uses causal “driver” language.

The evidence supports different claims:

| Evidence achieved | Maximum publication claim |
|---|---|
| Phase 08 DEG + Phase 18 KDA only | Internally supported network-associated candidate |
| Internal robustness + independent target-module replication | Replicated cell-type-associated candidate |
| Replication + genetics/proteomics/protein-network evidence | Multi-omic mechanistic candidate |
| Perturbation + rescue of predicted targets and phenotype | Functional driver |

STRING-db is one protein-network validation task. It cannot substitute for independent AD data, genetics, proteomics, or perturbation.

## 2. Candidate panel to validate first

For the labor-intensive replication, proteomics, protein-network, and
experimental work packages, start with seven candidates that test different
biological and methodological situations. This is a **purposefully balanced
pilot panel, not the seven genes with the smallest aggregate q values**.

WP5 human genetics is the explicit exception. Phase 19 assesses all 25
displayed genes in all 47 corresponding broad-network contexts because the
primary fine-mapping and precomputed colocalization extraction can be run in
one pass. The seven-gene prioritization does not limit the Phase 19 scientific
scope.

### How the seven were chosen

Every gene in the pilot first passed the formal Phase 18 selection gates in at least one broad network: usable-run coverage >= 0.80, at least one conservatively supporting run, aggregate ACAT q <= 0.05, and rank <= 5 within its broad-network × driver-class list. Conservative support means that the driver's neighborhood contained at least two other mitochondrial-query genes, had fold enrichment > 1, and had within-run q <= 0.05. The exact run- and aggregate-level evidence is stored in [`call_key_driver_returns.tsv`](../../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv).

The original six-gene subset was chosen to maximize information from the first validation round across five dimensions:

1. **Evidence role:** include an established positive control, internally strong candidates, and deliberately exploratory candidates.
2. **Biological breadth:** represent APOE/lipid biology, redox and tau proteostasis, lysosome–mTOR signaling, ribosomal stress, iron/ferroptosis, and chromatin regulation.
3. **Cell-type breadth:** cover astrocytes, excitatory neurons, inhibitory neurons, and OPCs.
4. **Methodological stress tests:** determine whether a recurrent ribosomal hub survives matched-null testing and whether sparse OPC signals reproduce independently.
5. **Experimental interpretability:** initially favor non-MT genes with potentially testable upstream mechanisms. Many selected MT genes are structural respiratory-chain components that may be valuable module sentinels but are harder to interpret as upstream regulators because their perturbation can cause nonspecific respiratory failure.

The all-gene WP5 screen then added **COX7C as the seventh candidate**. COX7C
is the only non-APOE candidate in the screened public xQTL summary with a
direct target-gene record, and it is displayed in both astrocyte and
inhibitory-neuron networks. The record is a weak, bulk-tissue sQTL signal, so
it raises COX7C's value as a cross-evidence validation test without establishing
cell-type specificity or causality. The same record projected onto two network
contexts is not two independent replications.

Consequently, the seven candidates do not enter validation with equal prior
confidence. APOE is a calibration control; COX7C is a genetics-informed but
still limited complex-IV candidate; SELENOW, LAMTOR5, and the
excitatory-neuron RPL11 result have comparatively strong internal or external
support; FTL and ANKRD11 are high-novelty, low-recurrence OPC hypotheses that
must replicate before receiving similar weight.

| Candidate | Broad network(s) to validate and Phase 18 basis | Why it is in the pilot |
|---|---|---|
| **APOE** | Astrocytes; aggregate q = 0.0127, four conservative-support runs across three fine cell types, with candidate retention in two of three assessable omissions | It is the established AD positive control. Successful recovery of its frozen astrocyte mitochondrial target module shows whether the validation pipeline can detect a known AD mechanism; the new claim is the target neighborhood, not discovery of APOE itself. |
| **COX7C** | Astrocytes and inhibitory neurons; aggregate q = 5.14 × 10^-4 and 6.24 × 10^-6, respectively. The displayed contexts contain two and six conservative-support runs; candidate-retention fractions are 0.67 and 1.00. | It adds a nuclear complex-IV/mitonuclear test and is the only non-APOE candidate with a direct target-gene xQTL record in the Tier 1 public screen. The genetic result is weak and bulk-tissue, so both displayed networks require separate replication and protein/complex-IV validation. |
| **SELENOW** | Excitatory neurons; aggregate q = 5.75 × 10^-6, 14 conservative-support runs across nine fine cell types in the selected context, and complete omission retention | It combines a strong, stable KDA signal with direct external AD-model evidence involving tau clearance and with redox/respiration biology. It is the externally reinforced novel-mechanism candidate. |
| **LAMTOR5** | Excitatory and inhibitory neurons; 17 conservative-support runs across 13 fine cell types in total, aggregate q = 0.00259 and 0.00414, respectively, and complete omission retention in both networks | It reproduces across two neuronal network types and provides a coherent, experimentally tractable lysosome–Ragulator–mTORC1 route to mitochondrial regulation, while remaining novel at the gene-specific AD level. |
| **RPL11** | Astrocytes, excitatory neurons, microglia, and oligodendrocytes; strongest in excitatory neurons (aggregate q = 1.84 × 10^-9, 20 conservative-support runs across 11 fine cell types, complete omission retention) | It is the broadest recurrent non-MT candidate and a deliberate specificity challenge. Validation must show that its result exceeds expression-, degree-, and ribosomal-class-matched nulls before it is interpreted as more than a ribosomal or high-connectivity module anchor. |
| **FTL** | OPCs; aggregate q = 2.19 × 10^-4 but only two conservative-support runs from one fine cell type; omission stability is not assessable | It tests a biologically plausible iron-storage/ferroptosis–mitochondria hypothesis in an understudied lineage. Its inclusion is exploratory: independent OPC localization and replication are prerequisites, because the current recurrence is sparse. |
| **ANKRD11** | OPCs; aggregate q = 7.12 × 10^-4 but only two conservative-support runs from one fine cell type; omission stability is not assessable | It is a mechanistically orthogonal, high-novelty chromatin-regulation hypothesis. It tests whether a new OPC-specific regulatory signal can reproduce, rather than whether a familiar mitochondrial or stress gene can be rediscovered. |

### Why other displayed genes were not in the first seven

Several omitted genes have strong Phase 18 statistics; omission does not mean
that they failed. RPS15, RPS13, RPLP1, RPL15, and RPL38 would overrepresent the
same ribosomal/translation theme, so RPL11 was chosen as the first
representative and as the most demanding hub-bias test. ATP6V1F and LAPTM4A
overlap the lysosomal theme, for which LAMTOR5 has broader neuronal support.
Most MT/OXPHOS candidates remain important for the full evidence matrix but are
not in the first panel because perturbing a structural respiratory-chain
component can produce an uninformative, generic respiratory defect. COX7C is
the deliberate exception: it is nuclear encoded, spans two displayed broad
networks, and now supplies a weak direct human-genetic mapping that can be
tested against protein stoichiometry and complex-IV assembly. FTL and ANKRD11
were retained despite weaker recurrence because validating or rejecting two
distinct OPC mechanisms will reveal whether the striking OPC aggregate signals
are independently reproducible or are consequences of the small OPC evidence
base.

After the pipeline works for these candidates, extend the computational evidence matrix to the remaining displayed genes. Reserve expensive experiments for two or three candidates.

## 3. Required analysis unit and frozen inputs

Use one validation unit per:

```text
key driver × broad cell-type network
```

Keep the run-level context attached:

```text
kda_run_id
fine_cell_type
sex
APOE group
signature_direction
KDA layer
predicted mitochondrial targets
```

The primary source is:

- [`call_key_driver_returns.tsv`](../../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv)

Before using any external resource, create:

```text
phase18_validation_candidate_manifest.tsv
```

Required columns:

```text
key_driver
broad_network
case_id
within_case_rank
kda_run_id
fine_cell_type
sex
apoe_group
signature_direction
final_layer
final_overlap_count
predicted_target_genes
aggregate_acat_q
conservative_support_count
coverage_fraction
stability_candidate_fraction
source_version
```

Rules:

- Freeze the candidate-context list before querying external databases.
- Freeze the exact predicted target list before external replication.
- Do not add or remove targets because they perform well or poorly externally.
- For MT drivers, remove the driver's guaranteed self-overlap.
- Treat a gene selected in two broad networks as two separate validation units.

## 4. Publication workflow and execution order

> **Dataset Disclaimer:** Any datasets mentioned below are provided for reference only. Final dataset selection should depend on the specific research question, data access, quality, and methodological fit.

Execute the work packages in this order:

```text
WP1  Freeze candidates and targets
 ↓
WP2  Internal KDA/network robustness
 ↓
WP3  Independent human transcriptomic replication
 ↓
WP4  APOE-model cross-species replication
 ↓
WP5  Human genetics
 ↓
WP6  Proteomics and pQTL–GWAS evidence
 ↓
WP7  STRING protein-network support
 ↓
WP8  Integrated ranking and candidate selection
 ↓
WP9  Perturbation and rescue
```

WP5–WP7 can run in parallel after WP1 is complete. Do not start WP9 until WP2–WP8 identify the strongest experimental candidates.

## 5. WP1 — Freeze candidates, contexts, and target sets

### What to do

1. Filter `call_key_driver_returns.tsv` to `top5_display == TRUE`.
2. Deduplicate to one row per `key_driver × broad_network × case_id` for the candidate manifest.
3. For each pilot candidate, retain run rows with `conservative_support == TRUE`.
4. Parse `published_overlap_items` into individual target genes.
5. Check the target count against `final_overlap_count` and `other_query_overlap`.
6. If an MT driver was self-excluded or `final_layer` differs from the published layer, reconstruct the final target list from the directed network at `final_layer` intersected with the matched mitochondrial query.
7. Create both:

   - a run-level target set; and
   - a driver × broad-network consensus target set with recurrence counts.

### Output

```text
phase18_validation_candidate_manifest.tsv
phase18_validation_run_targets.tsv
phase18_validation_consensus_targets.tsv
```

### QC checks

- No duplicate gene × network candidate units.
- Target count equals the final stored count.
- Every target maps to the original tested-gene background.
- MT self-overlap is removed.
- Every row retains its cell-type, group, and direction labels.

## 6. WP2 — Internal KDA and network robustness

### Question

Is each candidate stronger than comparable genes, or is it selected because it is highly expressed, highly connected, ribosomal, or part of a respiratory complex?

### How to do it

#### A. Leave-one-fine-cell-type-out stability

For each candidate × broad network:

1. omit one supporting fine cell type;
2. recompute the aggregate evidence and candidate decision;
3. repeat for all supporting fine cell types; and
4. report candidate retention fraction and worst rank.

Suggested publication criterion:

```text
candidate retained in >= 80% of assessable omissions
```

Report the exact fraction; do not force the criterion when very few omissions are assessable.

#### B. Network sensitivity

Repeat KDA under prespecified, defensible network edge-confidence or pruning settings. Report whether the candidate remains significant and whether its target set is stable.

#### C. Matched-driver null

For each selected driver:

1. choose control genes from the same Bayesian network;
2. match on expression, Bayesian in/out/total degree, neighborhood size, and driver functional class;
3. keep the real mitochondrial query fixed;
4. run at least 1,000 matched draws when feasible; and
5. compare KDA enrichment and recurrence with the selected driver.

Ribosomal drivers require a ribosomal-gene matched null. OXPHOS candidates require a respiratory-chain/complex matched null.

Use:

```text
empirical_p =
    (1 + number of null statistics >= observed statistic)
    /
    (1 + number of null draws)
```

Apply BH correction across the primary candidate × network tests.

#### D. Technical-covariate sensitivity

Test whether candidate expression and target-module scores remain associated with diagnosis after accounting for available technical variables such as:

- mitochondrial read fraction;
- RNA/nucleus quality;
- library size;
- inferred mitochondrial mass;
- mtDNA copy number, if available; and
- donor/batch effects.

Use donor-level models; do not treat nuclei as independent replicates.

### Pass criteria

A publication-priority candidate should:

- retain the existing Phase 18 coverage/support/ACAT gates;
- survive most assessable leave-one-out tests;
- remain credible under at least one alternative network setting;
- outperform matched null drivers after correction; and
- not be explained by one obvious technical covariate.

### Outputs

```text
phase18_internal_robustness.tsv
phase18_matched_driver_null.tsv
phase18_network_sensitivity.tsv
```

### Figure

One robustness heatmap with candidates as rows and stability, matched-null, and sensitivity metrics as columns.

## 7. WP3 — Independent human transcriptomic replication

### Question

Does an independent human AD cohort reproduce the candidate's predicted mitochondrial target module in the matched cell type?

This is the most important computational validation task.

### Required data

Select a reference candidate only if it has:

- independent AD and control donors;
- donor identifiers;
- compatible brain region;
- raw counts or valid normalized expression;
- cell types that can be mapped to the discovery labels;
- diagnosis and relevant covariates; and
- adequate coverage of the frozen target genes.

APOE- and sex-specific replication additionally requires verified APOE genotype and sex metadata with sufficient donors. Do not claim such replication without those fields.

### How to do it

1. Audit donor counts, metadata completeness, batch, brain region, and target coverage.
2. Perform dataset-specific QC and cell-type annotation; do not force original labels.
3. Aggregate expression by donor × cell type.
4. Use:

   - **DESeq2** for pseudobulk counts; or
   - **limma** for non-count normalized pseudobulk data.

5. Fit the matched AD-versus-control model with available covariates.
6. Test two prespecified endpoints:

   - candidate-gene expression; and
   - the complete frozen KDA target module.

7. For the target module, report:

   - number and fraction of targets measured;
   - ranked gene-set enrichment or prespecified donor-level module effect;
   - module effect size and 95% CI;
   - FDR;
   - target-level directional concordance; and
   - Spearman correlation between discovery and replication target effect sizes with bootstrap CI.

8. Fit formal disease × sex and disease × APOE interactions only when the replicate structure supports them.
9. If several compatible cohorts are available, meta-analyze effect sizes and report heterogeneity.

### Primary success criterion

The candidate's frozen target module should:

- be sufficiently measured to make the test meaningful;
- change in the same direction as discovery;
- meet the prespecified module-level FDR threshold; and
- not be driven by one donor or batch.

Candidate-gene DEG replication is supporting evidence, not a requirement: KDA does not require the driver itself to be differentially expressed.

### Outputs

```text
external_dataset_suitability.tsv
phase18_external_human_replication.tsv
phase18_external_target_effects.tsv
```

### Figure

- Forest plot of target-module effects by candidate and cell type.
- Discovery-versus-replication target-effect scatterplot.

## 8. WP4 — APOE-model cross-species replication

### Question

Does the human candidate-target module recur in the professor-provided APOE knock-in/model data?

### Required checks before analysis

Verify:

- APOE genotype/model design;
- disease and control groups;
- animal identifiers and biological replicates;
- age, sex, region, and batch;
- raw counts or valid analysis input;
- cell-type annotation quality; and
- human–mouse ortholog coverage.

### How to do it

1. Map frozen human targets to one-to-one mouse orthologs.
2. Report missing and ambiguous orthologs.
3. Map comparable cell types conservatively.
4. Aggregate by animal × cell type.
5. Fit the relevant genotype/disease contrast.
6. Test candidate expression and the frozen orthologous target module.
7. Report module effect, 95% CI, FDR, directional concordance, and human–mouse effect correlation.

### Pass criterion

Call the result cross-species support only if the orthologous target module changes coherently in the matched cell type using animals as replicates.

If only the pathway but not individual genes agrees, report pathway-level conservation rather than exact replication.

### Outputs

```text
apoe_model_suitability.tsv
phase18_cross_species_replication.tsv
phase18_human_mouse_ortholog_map.tsv
```

## 9. WP5 — Human genetic support

WP5 is implemented as a standalone next phase. Detailed plan:
[Phase 19 human genetic support overall plan](../../phase_19_genetic_support/overall_plan.md).
The Phase 19 plan is authoritative for scope, source freezing, assessability,
evidence grading, execution, and outputs.

### Question

Is inherited variation linked to the candidate associated with AD or a relevant AD phenotype?

Reference resources include [NIAGADS Alzheimer's GenomicsDB](https://www.niagads.org/genomics/), [NIAGADS/ADSP](https://www.niagads.org/), and the [NHGRI–EBI GWAS Catalog](https://www.ebi.ac.uk/gwas/). These are resource directions; candidate-specific suitability and data access must be verified.

### How to do it

For each candidate:

1. Search AD risk, age at onset, cognitive decline, and relevant biomarker GWAS.
2. Record study accession, ancestry, sample size, phenotype, lead variant, effect allele, effect size, P value, and correction status.
3. Determine whether the gene is:

   - merely nearest to the lead variant;
   - inside a credible set;
   - supported by a coding variant;
   - connected through relevant regulatory annotations; or
   - supported by brain/cell-type eQTL or sQTL colocalization.

4. Search ADSP/published sequencing evidence for rare-variant burden or damaging-variant association.
5. Record variant mask, frequency threshold, ancestry, multiple-testing correction, and replication status.

### Evidence grading

| Grade | Criterion |
|---|---|
| Strong | Fine-mapped coding evidence, replicated rare-variant burden, or well-supported AD–molecular-QTL colocalization |
| Moderate | AD locus with several convergent mappings to the candidate |
| Weak | Nearest-gene assignment or nominal uncorrected association |
| None found | No convincing evidence in the sources examined; not evidence that the gene has no role |

Do not describe a gene as “mutated in AD patients” merely because variants are present in cases.

For mtDNA-encoded candidates, examine mtDNA variation, heteroplasmy, copy number, and nuclear regulators rather than relying only on nuclear GWAS.

### Output

```text
results/minerva_production/19_genetic_support_tier1/genetic_support_evidence_summary.tsv
```

## 10. WP6 — Human proteomics and proteogenomics

### Question

Is the candidate protein or predicted target-protein module altered in human AD, and does genetically regulated protein abundance share an AD risk signal?

[Agora](https://agora.adknowledgeportal.org/about) and the [AD Knowledge Portal](https://adknowledgeportal.synapse.org/) are reference directions for AD multi-omic evidence. Verify cohort independence, tissue, platform, protein coverage, metadata, and access before analysis.

### A. Protein-abundance analysis

For each candidate and cohort:

1. map the gene to stable protein identifiers;
2. check peptide/probe uniqueness and protein missingness;
3. record brain region, platform, case/control counts, and cell-type resolution;
4. fit an AD-versus-control model with study-appropriate covariates;
5. report effect size, SE, 95% CI, raw P value, and FDR;
6. test replication across independent cohorts; and
7. test the frozen target-protein module when individual target coverage permits.

Bulk-tissue support should be labeled as such. Use spatial or cell-type-resolved evidence when available to confirm OPC, astrocyte, or vascular localization.

### B. Protein-complex/function analysis

For OXPHOS candidates, prioritize:

- complex assembly and enzymatic activity;
- supercomplex composition;
- mitonuclear stoichiometry;
- mitochondrial mass;
- mtDNA quantity/heteroplasmy; and
- respiration.

Protein abundance alone is insufficient to show functional respiratory impairment.

### C. pQTL–AD-GWAS colocalization

When a suitable cis-pQTL exists:

1. harmonize genome build, variants, effect alleles, and ancestry;
2. confirm adequate pQTL and AD signals in the locus;
3. account for multiple independent signals;
4. run colocalization and report all posterior hypotheses;
5. test sensitivity to priors and locus definition;
6. inspect coding variants for assay-binding artifacts; and
7. report the allele → protein → AD-risk direction.

A high shared-signal posterior supports a shared variant, not proven mediation.

### Outputs

```text
phase18_human_proteomic_evidence.tsv
phase18_protein_module_results.tsv
phase18_pqtl_gwas_colocalization.tsv
```

### Figure

Protein-effect forest plot plus locus plot for any convincing colocalization.

## 11. WP7 — STRING protein-network support

### Question

Are the selected driver and its exact KDA-predicted mitochondrial targets connected by prior experimental or curated protein evidence?

### Correct input

For the primary analysis, submit separately for every matched context:

```text
one selected key driver
    +
the exact mitochondrial DEG targets in that driver's KDA neighborhood
```

Do not pool all DEGs, all drivers, and all Bayesian-network nodes.

### How to do it

1. Use Homo sapiens (`species = 9606`).
2. Run an input-only physical network:

   ```text
   required score: approximately 0.700
   first-shell additions: 0
   second-shell additions: 0
   primary evidence: experiments and curated databases
   ```

3. Run a separate functional network for broader pathway concordance.
4. Export identifier mapping and all evidence-channel scores.
5. Record:

   - direct driver–target edges;
   - fraction of targets directly connected;
   - input-only two-step connections;
   - observed and expected edges;
   - PPI-enrichment P value and corrected q value; and
   - functional enrichment with an appropriate tested-gene background.

6. Compare with:

   - expression/Bayesian-degree/STRING-degree/function-matched control drivers; and
   - expression/detectability/STRING-degree/function-matched mitochondrial target sets.

7. Use at least 1,000 matched null draws when feasible and calculate empirical P values.
8. Add connector proteins only in a separate exploratory analysis and label them as new hypotheses.

Use the official STRING [network/evidence documentation](https://string-db.org/help/scores/) and [API](https://string-db.org/help/api/). Automated requests should use `scripts/rest_request.py`, POST requests, `https://string-db.org/api/json`, and a stable project `caller_identity`.

### Pass criterion

STRING provides useful support when driver–target experimental/database connectivity exceeds matched nulls after correction.

Interpretation rules:

- A connected target module with an isolated driver validates the module, not the driver.
- Ribosomal/OXPHOS complex membership is module evidence, not unique-driver evidence.
- Coexpression- or text-mining-only edges are exploratory.
- Missing STRING edges are absence of database support, not biological contradiction.

### Outputs

```text
phase18_string_input_sets.tsv
phase18_string_id_mapping.tsv
phase18_string_edges.tsv
phase18_string_summary.tsv
phase18_string_matched_null.tsv
```

### Figure

Paired panel:

- left: original directed KDA neighborhood;
- right: input-only STRING protein network;
- identical node colors; and
- SVG export for Cytoscape editing.

## 12. WP8 — Integrate evidence and select experimental candidates

### Evidence matrix

Create:

```text
phase18_integrated_validation_matrix.tsv
```

One row per `key_driver × broad_network` with:

```text
internal_robustness
external_human_replication
cross_species_replication
human_genetic_grade
human_proteomic_grade
pqtl_gwas_grade
string_grade
main_contradiction
main_missing_evidence
publication_tier
recommended_action
```

Use explicit states:

```text
support
partial_support
contradiction
inconclusive
not_measured
not_evaluated
```

Do not convert database presence into an arbitrary point score. Do not count two databases using the same underlying study as independent evidence.

### Publication tiers

| Tier | Required evidence | Action |
|---|---|---|
| A | Robust internal result + independent human/model replication + strong orthogonal evidence | Advance to perturbation and main manuscript |
| B | Robust internal result + one external/orthogonal layer | Main or secondary candidate; resolve missing evidence |
| C | Internal robustness only | Keep as exploratory/supplemental |
| D | Module signal but individual-driver support fails | Report at pathway/module level |
| E | Fails robustness or shows convincing contradiction | Do not prioritize |

### Experimental selection

Choose two or three candidates:

1. one positive control: **APOE**;
2. one externally reinforced or mechanistically focused candidate: **SELENOW or LAMTOR5**; and
3. one specificity test: **RPL11**, only if it exceeds ribosomal matched nulls.

FTL or ANKRD11 can replace the third candidate if OPC replication is especially strong.

## 13. WP9 — Perturbation and rescue

### Requirement for causal publication language

Use perturbation only after the frozen target module and relevant cell context are selected.

### How to do it

1. Use the relevant cell model: astrocyte, excitatory neuron, inhibitory neuron, or OPC.
2. Use APOE-isogenic backgrounds when the claim is APOE-dependent.
3. Use graded CRISPRi/CRISPRa or titratable perturbation, especially for essential ribosomal/OXPHOS genes.
4. Use at least two independent reagents.
5. Include non-targeting, pathway-positive, and general-toxicity controls.
6. Use independent donors, clones, or differentiations as biological replicates.
7. Measure early time points before generalized stress dominates.
8. Test the frozen target module as the primary molecular endpoint.
9. Measure candidate-specific pathway and mitochondrial phenotypes.
10. Rescue with an sgRNA-resistant construct or appropriate pathway rescue.

### Statistical analysis

- Biological replicate—not well—is the experimental unit.
- Use a model containing perturbation, genotype, and their interaction when applicable.
- Include batch/differentiation effects.
- Report effect size and 95% CI.
- Correct target-level tests for multiplicity.
- Treat the frozen target-module test as primary.

### Functional-driver success criteria

All should be satisfied:

1. candidate changes at RNA/protein level;
2. frozen target module changes reproducibly;
3. relevant mitochondrial/pathway phenotype changes;
4. effect occurs without generalized toxicity;
5. independent reagent reproduces the result; and
6. rescue reverses module and phenotype effects.

### Outputs

```text
phase18_perturbation_results.tsv
phase18_rescue_results.tsv
```

## 14. Publication figure plan

| Figure | Required content |
|---|---|
| Figure 1 | Study workflow, DEG/KDA design, and frozen candidate-selection process |
| Figure 2 | Main cell-type/sex/APOE mitochondrial DEG results |
| Figure 3 | Phase 18 candidate atlas and internal robustness/matched-null evidence |
| Figure 4 | Independent human and APOE-model target-module replication |
| Figure 5 | Genetic, proteomic, pQTL, and STRING evidence matrix |
| Figure 6 | Paired directed KDA and STRING networks for top candidates |
| Figure 7 | Perturbation, target-module response, mitochondrial phenotype, and rescue |

If experiments are not available, stop at “multi-omic network-associated candidate” and do not use causal-driver language in the title, abstract, or discussion.

## 15. Immediate task list

### Priority 0 — do first

- [ ] Generate the frozen candidate and target manifests.
- [ ] Confirm final target lists for MT self-excluded rows.
- [ ] Complete leave-one-fine-cell-type-out and matched-driver null analyses.
- [ ] Create the external-data suitability template.
- [ ] Obtain full metadata for the professor-provided APOE model.

### Priority 1 — publication-critical computational validation

- [ ] Select and audit at least one independent human AD transcriptomic reference candidate.
- [ ] Run donor-level target-module replication.
- [ ] Run the APOE-model orthologous module analysis if suitable.
- [ ] Complete Phase 19 genetic support for all 25 genes and all 47
  corresponding broad-network contexts.
- [ ] Compile Agora/AD Knowledge Portal protein evidence for the seven candidates.
- [ ] Run pQTL–GWAS colocalization where both signals are adequate.
- [ ] Run context-matched STRING analyses and matched nulls.

### Priority 2 — integrate and decide

- [ ] Build the integrated validation matrix.
- [ ] Assign publication tiers.
- [ ] Select two or three experimental candidates.
- [ ] Freeze experimental hypotheses and endpoints.

### Priority 3 — functional validation

- [ ] Perform graded perturbation with two reagents.
- [ ] Measure the frozen target module and candidate-specific phenotype.
- [ ] Perform rescue.
- [ ] Update publication claims according to the achieved evidence level.

## 16. Main risks and fallback

| Risk | Required mitigation |
|---|---|
| Runs reuse the same broad network | Do not call recurrence independent replication; add external networks/data |
| Nuclei treated as replicates | Use donor-level pseudobulk |
| Sex/APOE subgroup overinterpretation | Fit formal interaction terms |
| Ribosomal/OXPHOS hub bias | Use expression-, degree-, and class-matched nulls |
| External cell types do not match | Document mapping confidence; report pathway-level rather than exact replication |
| Bulk protein signal reflects cell composition | Add cell-type/spatial evidence or state limitation |
| GWAS nearest-gene overclaim | Require fine mapping, functional mapping, or colocalization |
| STRING treated as AD-specific | Restrict claim to prior protein-network support |
| Perturbation causes general toxicity | Use graded doses, early time points, global-stress controls, and rescue |

If individual candidates fail but their target modules replicate, publish the system-level result: cell-type-specific ribosomal stress, lysosome–mTOR/mitophagy, iron handling, transport, or mitonuclear respiratory remodeling. Do not force an individual-driver conclusion.

## 17. Verified resources and related project documents

- [Phase 18 key-driver selection process](../../phase_18_key_driver_selection/key_driver_selection_process.md)
- [Phase 18 initial gene-by-gene interpretation](phase18_key_driver_gene_by_gene_initial_analysis.md)
- [Professor's notes after the 2026-08-12 presentation](../../email_notes/notes_after_08122026_presentation.txt)
- STRING [network types/evidence channels](https://string-db.org/help/scores/) and [API](https://string-db.org/help/api/)
- [Agora](https://agora.adknowledgeportal.org/about)
- [AD Knowledge Portal](https://adknowledgeportal.synapse.org/)
- [NIAGADS Alzheimer's GenomicsDB](https://www.niagads.org/genomics/)
- [NIAGADS](https://www.niagads.org/)
- [NHGRI–EBI GWAS Catalog](https://www.ebi.ac.uk/gwas/)
- Giambartolomei C, et al. Bayesian test for colocalisation between pairs of genetic association studies using summary statistics. *PLoS Genetics*. 2014. [doi:10.1371/journal.pgen.1004383](https://doi.org/10.1371/journal.pgen.1004383).
