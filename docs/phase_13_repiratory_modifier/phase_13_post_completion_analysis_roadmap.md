# Post-Phase 13 Analysis Roadmap

## Status and purpose

This document explains what can be analyzed **after Phase 13 has finished and
its production bundle has passed every technical validation check**.

Roadmap status: **planning document; it does not authorize or run an
analysis**.

Phase 13 tests Claim 1 (C1):

> Within a broad brain cell context, does sex or APOE change the
> Alzheimer-disease-versus-NCI difference in a prespecified mitochondrial
> expression program?

Here, NCI means the comparison group labeled no cognitive impairment. It does
not mean that the donor was free of Alzheimer-related brain pathology.

Finishing Phase 13 has two different meanings:

1. **Technical completion:** the expected files exist, all checks pass, and the
   production bundle reports `validation_status = validated_complete`.
2. **Scientific outcome:** C1 may be supported, provisional, inconclusive,
   precisely unsupported, or not testable.

Technical completion does not guarantee a positive scientific result.

As of 2026-08-09:

- `results/minerva_production/13_respiratory_modifier/` is not present;
- the Phase 13 prose plan still says “draft/not approved,” while its YAML says
  `definitions_approved = true` and `definitions_frozen = true`; this status
  mismatch must be reconciled before production;
- two Phase 13 prose links point to companion filenames that are not present;
  repair or replace those links before final plan approval;
- Phase 14 has config/script/tests and its plan records a successful synthetic
  local pilot, but Minerva production remains unapproved and absent; and
- Phase 15 now has config/script/tests and its plan records a successful
  synthetic local pilot, but Minerva production remains unapproved and absent.

This roadmap is therefore prospective. It describes what should happen once
the Phase 13 production dependency exists.

## Quick answer

After Phase 13, the work should proceed in this order:

```text
Validated Phase 13 production bundle
                 |
                 v
Lock and explain the C1 result; make the Phase 13 evidence figure
                 |
                 +----------------------+----------------------+
                 |                      |                      |
                 v                      v                      v
       Phase 14 / Claim 2     Phase 15 / Claim 3     C4-C6 phenotype tests
       compare contexts       test mtDNA-nuclear     test the three candidate
                              coupling               systems in donor data
                 |                      |                      |
                 +----------------------+----------------------+
                                        |
                                        v
                         Hold a locked C1-C6 evidence review
                               |
                               v
        Run C7 network validation only for authorized candidates
                               |
                               v
         Replicate frozen survivors in independent RNA/protein data
                               |
                               v
          Consider experiments only for the strongest survivors
```

Phase 14, Phase 15, and the C4-C6 donor-level phenotype analyses can be
developed as parallel branches after validated Phase 13. Phase 15 does not
depend on Phase 14 and must not be restricted to positive Phase 13 rows.
Candidate convergence wording may still require the appropriate Phase 14 or
Phase 15 evidence at the locked review.

Do **not** automatically start new KDA simulations merely because Phase 12
produced attractive candidates. Candidate network validation is allowed only
after the corresponding donor-level candidate phenotype passes its own gate.

---

## A. Study intent summary

### A.1 Biological objective

The project asks whether Alzheimer disease is associated with a coordinated
mitochondrial RNA-expression change that:

1. differs by recorded sex or APOE group;
2. occurs in particular broad brain cell contexts;
3. changes the relationship between mitochondrial-DNA and nuclear-DNA
   respiratory expression; and
4. is reproducibly associated with one or more network-nominated candidate
   systems.

Phase 13 addresses only the first part within each broad context. Later phases
must supply evidence for the other parts.

### A.2 Why single-nucleus data add value

Bulk brain RNA combines many cell populations. A mitochondrial signal in
astrocytes may be hidden or diluted by an opposite neuronal signal.

Single-nucleus data allow the project to create a separate donor-level profile
for each broad cell context. The donor remains the independent biological
sample. Individual nuclei are not treated as separate people.

### A.3 Main scope assumptions

This roadmap assumes:

- Phase 13 used the frozen ROSMAP analytic cohort and metadata;
- raw nucleus counts were summed into one donor-by-context profile;
- all seven broad contexts were analyzed;
- all seven direct sex/APOE modifier contrasts were preserved;
- all four frozen mitochondrial programs were tested;
- all 196 planned rows were retained, including negative and untestable rows;
- Phase 13 definitions were not changed after opening the effects; and
- the final Phase 13 bundle is independently validated.

If any assumption fails, stop and repair or formally version the dependency
before using this roadmap.

### A.4 Essential terms, explained before they are used

| Term | Plain-language meaning |
|---|---|
| Donor | One person who contributed brain tissue. Donors, not nuclei, determine the statistical sample size. |
| Nucleus / nuclei | A cell nucleus measured by single-nucleus RNA sequencing. Many nuclei may come from the same donor. |
| Pseudobulk profile | Raw RNA counts from all eligible nuclei of one donor and one cell context added together. The result is one donor-level sample. |
| Broad cell context | A large cell class such as astrocytes, excitatory neurons, inhibitory neurons, immune cells, OPCs, oligodendrocytes, or vasculature. |
| Fine cell type | A smaller transcriptomic subtype nested within a broad context. Fine types are useful for localization but have fewer nuclei and donors. |
| Gene module / program | A gene set chosen in advance because its members perform related biological jobs. |
| AD effect | The adjusted expression difference between AD and NCI donors within one sex-by-APOE group. |
| Modifier / interaction | A direct test of whether two AD effects differ. It is a difference-of-differences, not a comparison of two P values. |
| Estimate | The fitted size and direction of an effect. Positive and negative directions must be defined for every comparison. |
| Confidence interval (CI) | A range showing uncertainty around an estimate. A wide CI means the data do not locate the effect precisely. |
| P value | Evidence against a specific statistical null before adjusting for the number of questions tested. |
| q value | A P value adjusted because many related questions were tested. |
| Gate | A rule decided before reviewing results that determines whether a claim may advance. |
| Supported | Every required effect, uncertainty, sample-size, and stability rule passed. |
| Provisional | The pattern may be present, but donor counts or another required condition are too weak for confirmation. |
| Inconclusive | The data cannot distinguish a meaningful result from no meaningful result. This is not the same as a negative result. |
| Precise null | The CI is narrow enough to rule out the project-defined meaningful effect size. |
| Internal support | Evidence found and stress-tested in the same ROSMAP donor cohort. |
| Independent replication | The frozen result appears in different donors in another suitable cohort. |
| Orthogonal support | Support from a different type of measurement, such as protein rather than RNA. |
| Candidate system | A network-nominated gene association plus its named expression readout and local biological program. |
| Target-excluded module | A module score recalculated after removing the named gene, so the gene cannot manufacture its own module support. |
| KDA | Key-driver analysis: a network procedure asking whether a candidate lies unusually close to a query gene set. |
| Network hub | A gene with many network connections. Hubs can look important even when they are not specific to the disease signal. |
| Causality | Evidence that changing one factor produces a biological outcome. RNA associations and networks do not establish causality. |

### A.5 What Phase 13 can and cannot establish

If a direct respiratory row passes, Phase 13 may support wording such as:

> In ROSMAP broad excitatory-neuron profiles, the AD-associated nuclear OXPHOS
> expression effect differed between female APOE e4 and female APOE e33
> donors.

Phase 13 alone cannot establish:

- that the effect differs statistically between cell contexts;
- that mitochondrial-DNA and nuclear-DNA expression became uncoupled;
- that any candidate gene regulates the program;
- that mitochondrial respiration, ATP production, or mitochondrial mass
  changed;
- that the result replicates in different donors; or
- that the association is causal.

---

## B. Best-fit study pattern

### B.1 Dominant pattern: key-cell and key-program prioritization

The best-fit design is a **key-cell/key-program prioritization study**.

The goal is not to build another general cell atlas. The goal is to identify:

- which mitochondrial program carries the AD-related modifier;
- which sex/APOE comparison carries it;
- which broad cell context shows it;
- whether the mtDNA-nuclear relationship also changes; and
- which candidate systems deserve expensive validation.

### B.2 Supporting pattern: candidate target discovery

A secondary pattern is **candidate target discovery** for:

- `APOE–TUFM`;
- `LAMTOR5–ATP5IF1`; and
- `GABARAPL2–CHCHD2/PARK7`.

This candidate layer is subordinate to the biological result. The candidates
cannot rescue a failed C1, C2, or C3 clause.

The dash in a name such as `APOE–TUFM` means “network-nominated association.”
It is not a causal arrow and does not specify molecular direction.

### B.3 Patterns not recommended by default

The following analyses should not be added merely because single-nucleus data
are available:

- trajectory or pseudotime, because the central question is not an ordered
  lineage transition;
- RNA velocity, because the central design does not require dynamic splicing
  inference;
- broad cell-cell communication screens, because they do not directly test
  C1-C7;
- an all-54-fine-type primary screen, because it would greatly increase the
  testing burden and reduce donor-level precision; or
- a new pathway catalogue searched until something becomes significant.

These could become separate projects only after a specific biological reason,
data requirement, and multiplicity plan are approved.

---

## C. Four workload configurations

Each higher configuration contains all work in the lower configuration.

| Configuration | Main goal | Required data | Included analyses | Validation level | Main deliverables | Strength | Limitation |
|---|---|---|---|---|---|---|---|
| **Lite** | Finish and explain C1 correctly | Validated Phase 13 production bundle | Locked C1 review, all 196 rows, donor plots, forest plots, stability panels, gene contributors | Within-ROSMAP consistency | Phase 13 evidence table and Figure 1 | Fastest defensible result package | Cannot support cell-context heterogeneity, mitonuclear coupling, network robustness, or replication |
| **Standard — recommended** | Establish the core biological result and one feasible validation layer | Lite inputs plus Phase 14/15 implementations, targeted candidate definitions, and a verified external/orthogonal feasibility audit | Lite + Phase 14/C2 + Phase 15/C3 + C4-C6 donor phenotype tests + locked C1-C6 review + one frozen external/orthogonal check when a suitable resource is verified | Strong within-cohort confirmation; one outside/orthogonal layer when feasible | Core Figures 1-4, claim matrix, candidate authorization table, and validation feasibility/result | Directly tests important clauses before expensive network work | If no suitable outside layer exists, label this an internally complete Standard core, not independent replication |
| **Advanced** | Validate surviving systems and deepen generalization | Standard inputs plus networks, fine-cell pseudobulk, and additional suitable independent/orthogonal resources | Standard + focused fine localization + C7 network controls + independent RNA and/or protein validation beyond the first feasible layer | Internal robustness, network calibration, and cross-donor/cross-modality evidence | Full computational figure set and robust-driver table | Strong computational paper structure | Network results still do not establish causality; external metadata may be inadequate |
| **Publication+** | Build a multi-layer mechanistic manuscript | Advanced inputs plus suitable protein data and feasible experimental resources | Advanced + protein support + an additional independent/orthogonal layer + perturbation/rescue for strongest survivors | Cross-dataset, cross-modality, and potentially functional evidence | Full manuscript package and experimental figure | Strongest claim potential | Highest cost, longest duration, and dependent on resources not yet confirmed |

---

## D. Recommended primary plan

The recommended plan is **Standard**, followed by Advanced work only for
survivors. Execute Standard in two stages:

1. complete the ROSMAP internal core through the locked C1-C6 review; and
2. freeze and run one external or orthogonal validation layer only when the
   feasibility audit identifies a suitable resource.

If no suitable external/orthogonal resource is available, complete and label
the work as the **internally complete Standard core** rather than claiming
replication.

### D.1 Why Standard is the correct next target

Phase 13 alone establishes only a within-context modifier result. The central
story also needs to know:

- whether the modifier actually differs across cell contexts (C2);
- whether mtDNA and nuclear respiratory expression change their relationship
  (C3); and
- whether each candidate system has the expected donor-level phenotype
  (C4-C6).

Phase 14 and Phase 15 reuse Phase 13 data but answer different questions. They
are therefore higher-value next steps than a new broad discovery screen.

### D.2 Why Lite is still useful

Lite is the minimum defensible stopping point when time or computing is
limited. It produces a complete C1 result and figure without overstating what
Phase 13 proved.

### D.3 Why Advanced is not the default first action

C7 network null simulations, alternative-network construction, and external
replication are expensive. Running them before C1-C6 are reviewed risks
spending substantial effort on candidates that lack a donor-level phenotype.

### D.4 The central stop rule

Do not begin C7 for a candidate unless:

1. its exact C4, C5, or C6 phenotype gate passed;
2. the relevant core biological endpoint is supported;
3. the exact context and comparison are frozen; and
4. the authorization is recorded in a machine-readable manifest.

---

## E. Data strategy and example dataset directions

### E.1 Required immediate data: the validated Phase 13 bundle

Required root:

```text
results/minerva_production/13_respiratory_modifier/
```

The first check is:

```text
respiratory_status.tsv:
    validation_status = validated_complete
```

Directory existence alone is not sufficient. All artifact hashes, schemas,
row counts, unique keys, and blocking checks must reproduce.

### E.2 Phase 13 files and their downstream jobs

| Phase 13 file | Main downstream use |
|---|---|
| `respiratory_claim_summary.tsv` | Overall C1 result and allowed wording |
| `respiratory_gate_decisions.tsv` | Complete component-by-component status for all 196 rows |
| `respiratory_module_results.tsv` | Direct module modifier estimates, CIs, P/q values, counts, eligibility, and model status; final scientific status comes from the gate table |
| `respiratory_module_stratum_effects.tsv` | Six component AD-minus-NCI effects used to explain each modifier |
| `respiratory_donor_module_scores.tsv.gz` | Donor-level plots and Phase 14/15 score inputs |
| `respiratory_gene_interaction_results.tsv.gz` | Supporting gene-level direct modifier results |
| `respiratory_gene_stratum_effects.tsv.gz` | Supporting within-stratum gene effects |
| `respiratory_camera_results.tsv` | Correlation-aware gene-set evidence |
| `respiratory_stability_summary.tsv` | Bootstrap, leave-one-donor-out, balance, threshold, QC, and omission summaries |
| `respiratory_stability_replicates.tsv.gz` | Detailed stability distributions and donor influence |
| `respiratory_module_reliability.tsv` | Mean-z/PC1 agreement and gene-concentration checks |
| `respiratory_pc1_loadings.tsv.gz` | Reconstruct the alternative module score |
| `respiratory_module_coverage.tsv` | Determine which frozen genes were measured and admitted |
| `respiratory_donor_samples.tsv.gz` | Donor group, nucleus count, study, and QC information |
| `respiratory_pseudobulk_counts.rds` | Raw broad-context donor counts for reconstruction and resampling |
| `respiratory_expression_bundle.rds` | Tested genes, normalized expression, designs, and backgrounds |
| `respiratory_checks.tsv` and `respiratory_artifacts.tsv` | Technical and provenance validation |

### E.3 Additional existing data needed for specific branches

| Branch | Additional required data |
|---|---|
| Phase 14 | No new donors; needs the validated Phase 13 scores, memberships, donor metadata, and reliability tables |
| Phase 15 | No new donors; needs the Phase 13 mtDNA and nuclear OXPHOS scores, counts, expression bundle, mappings, and QC fields |
| Fine-type localization | Validated Phase 07 donor-by-fine-type pseudobulk counts and fine-type eligibility |
| C4-C6 candidate tests | Phase 13/07 gene-level data plus frozen candidate genes, target-excluded modules, contexts, contrasts, and directions |
| C7 network validation | Complete cell-matched KDA/network results, exact network background, candidate authorization rows, and data for one donor-level alternative network |
| External RNA replication | A different-donor RNA cohort with suitable diagnosis, donor ID, cell-class, sex, APOE, covariate, and gene-coverage information |
| Protein support | A protein dataset with donor mapping, relevant covariates, and measured coverage of the frozen modules/candidates |
| Functional testing | An appropriate cell model, perturbation and rescue design, biological replicates, and mitochondrial functional readouts |

### E.4 External dataset direction

The deep-dive plan names SEA-AD as a possible independent single-nucleus RNA
reference candidate. This is a **candidate direction only**, not a guarantee
that the required sex/APOE groups, region, diagnosis definitions, donor counts,
or gene coverage are adequate.

Before external testing, create a feasibility table containing:

```text
resource_id
independent_donors
brain_region
diagnosis_definition
recorded_sex_available
APOE_available
donor_id_available
raw_or_summary_data_available
cell_class_mapping_possible
required_group_counts
module_gene_coverage
candidate_gene_coverage
overlap_with_ROSMAP_donors
permitted_claim
blocking_reason
```

If APOE or required group sizes are inadequate, an external resource may test
the broad respiratory or mitonuclear program but cannot replicate the exact
sex/APOE modifier.

### E.5 External-data risks

- another cohort may use a different brain region;
- AD and NCI definitions may differ;
- cell-type labels may not map exactly;
- APOE or sex metadata may be missing;
- small subgroup counts may make the modifier untestable;
- RNA preparation and sequencing may affect mtDNA transcripts differently;
- some candidate genes or proteins may not be measured; and
- overlapping donors provide another modality, not independent replication.

---

## F. Core analysis modules and method choices

| Analysis module | Priority | Purpose | Main method/design | Important constraint |
|---|---:|---|---|---|
| Locked Phase 13 review | Necessary | Determine exactly what C1 supports | Read the complete gate, result, stability, and claim tables; no refitting | Do not select only attractive rows |
| Phase 13 evidence figures | Necessary | Communicate effects, uncertainty, donors, and robustness | Signed heatmap, forest plot, donor score plot, bootstrap/LOO panel | Figures must not change the gate or analysis population |
| Phase 14 modifier heterogeneity | Necessary for between-context wording | Test whether a modifier differs directly between broad contexts | Repeated-donor joint mixed model with formal context-by-modifier contrasts | Different P values across contexts are not a direct test |
| Phase 15 mitonuclear coupling | Recommended central analysis | Test whether mtDNA and nuclear respiratory expression change their relationship | Difference score, cross-fitted NCI residual, and direct slope-change models | RNA relationship is not mitochondrial functional measurement |
| C4-C6 candidate phenotype tests | Recommended | Test named partners and target-excluded local programs in exact contexts | Donor-level direct modifier effects, module scores, CIs, and stability | Candidate expression itself need not be a DEG; correlation is not mediation |
| Focused fine-type localization | Optional after broad result | Locate a broad signal in prespecified subtypes | Donor pseudobulk models in a small frozen fine-type family | Fine types cannot rescue a failed broad result |
| Mitochondrial selectivity analysis | Optional claim-specific test | Ask whether mitochondrial change is greater than comparable nonmitochondrial change | Expression-, detection-, length-, and size-matched nonmitochondrial gene sets | Needed only for “mitochondrial-selective” wording |
| C7 network validation | Conditional | Test whether a candidate survives network bias controls | Self-excluded KDA, query-matched nulls, topology-matched nulls, edge perturbation, alternative donor network | A robust network association is still not causal |
| Independent RNA replication | Conditional | Test a frozen result in different donors | Frozen donor-level modules, mapped broad classes, direct contrasts when powered | No rediscovery or pathway switching in validation data |
| Protein support | Advanced | Test the same biological idea with a different measurement type | Frozen module/candidate protein effects with coverage reporting | `not_measured` is different from `tested_unsupported` |
| Functional perturbation | Publication+ | Test causal direction for strongest candidates | Loss/gain of function plus rescue and mitochondrial functional readouts | Must have biological replicates, toxicity controls, and a context-relevant model |

### F.1 Why Phase 14 and Phase 15 are separate

Phase 14 asks:

```text
Does the Phase 13 modifier differ between context A and context B?
```

Phase 15 asks:

```text
Does the relationship between mtDNA and nuclear respiratory expression change?
```

One can pass while the other fails. Neither substitutes for the other.

### F.2 Why focused fine-type work is not the primary next test

Broad contexts retain more donors and counts. Fine types are valuable for
localization only after the broad evidence is locked. Searching all fine types
first would increase false-positive risk and make low-powered results easier to
overinterpret.

### F.3 Methods that are deliberately not automatic additions

- trajectory and RNA velocity;
- general cell-cell communication analysis;
- regulon analysis across every cell type;
- a new all-pathway scan;
- unplanned three-way interactions;
- an all-54-cell primary family; and
- combining C4-C6 into one score that lets one strong candidate hide two weak
  candidates.

---

## G. Validation and extension layers

| Evidence layer | Example in this project | What it adds | What it does not add |
|---|---|---|---|
| Within-dataset consistency | Phase 13 direct tests and complete result rows | Shows the planned pattern exists in ROSMAP | Independent replication |
| Alternative analytic robustness | Bootstrap, leave-one-donor-out, PC1, 20/50-nucleus, balance, QC, omission checks | Shows the result is not dependent on one donor or reasonable analysis choice | A new cohort or causal evidence |
| New same-cohort claim test | Phase 14 or Phase 15 | Tests a distinct clause using the same donors | Independent validation |
| Alternative network robustness | C7 matched nulls, perturbation, donor-level coexpression network | Shows a network nomination is not easily explained by query composition or hub status | Molecular direction or causality |
| Cross-dataset RNA replication | Frozen result in a suitable different-donor RNA cohort | Shows generalization beyond ROSMAP donors | Protein or functional confirmation |
| Orthogonal protein support | Frozen program/candidate measured as protein | Shows support from a different measurement type | Independent replication if donors overlap |
| Functional perturbation and rescue | Alter candidate, measure predicted partner/program and mitochondrial phenotype, then rescue | Can support causal wording if well designed | Human-cohort generalization by itself |

The evidence layers must remain labeled separately. Three analyses performed on
the same ROSMAP donors are not three independent replications.

---

## H. Step-by-step workflow

> **Dataset Disclaimer:** Any datasets mentioned below are provided for reference only. Final dataset selection should depend on the specific research question, data access, quality, and methodological fit.

### H.0 Output-location rule

Treat the validated Phase 13 production bundle as immutable. A downstream
review or figure workflow must read it but must not add, replace, or edit files
inside it.

Until a downstream implementation contract freezes exact directories, paths
below use:

```text
results/<version>/post_phase13_review/
results/<version>/candidates/
results/<version>/kda/
results/<version>/networks/
results/<version>/validation/
```

`<version>` is a required versioned output root, not a literal final folder
name. The implementing plan must replace it before execution. The output-only
Phase 13 figure package is the exception and uses the dedicated separate root
defined in Task H.3.

### H.1 Task 1: validate the complete Phase 13 dependency

**Question answered**

Is Phase 13 technically safe to use as the source for downstream analyses?

**Why this is necessary**

A downstream analysis cannot be more trustworthy than its input. A directory
can exist while containing partial, mismatched, or stale files.

**Inputs**

- `respiratory_status.tsv`;
- `respiratory_artifacts.tsv`;
- `respiratory_checks.tsv`;
- all Phase 13 manifests;
- every scientific output declared by the Phase 13 artifact manifest; and
- the Phase 13 implementation/configuration hashes.

**Exactly what to do**

1. Require `validation_status = validated_complete`.
2. Confirm exactly 32 declared output files and no undeclared scientific
   artifact or subdirectory.
3. Confirm all nine Phase 13 stages completed successfully.
4. Confirm the artifact manifest has the intended 30 artifact rows: it hashes
   every declared artifact except itself and `respiratory_status.tsv`.
5. Recalculate every SHA-256 hash in `respiratory_artifacts.tsv`, then verify
   the status-file hash of the completed artifact manifest.
6. Require all blocking checks to pass.
7. Confirm exactly seven broad contexts.
8. Confirm exactly seven modifier contrasts.
9. Confirm exactly four modules and 273 module-membership rows.
10. Confirm exactly 196 structural test rows:

   ```text
   7 contexts × 7 modifiers × 4 modules = 196
   ```

11. Confirm that the test manifest, module results, `camera` results, stability
    summary, and gate decisions contain the same unique 196 `test_id` values.
12. Confirm exactly 168 module stratum rows and unique
    `context_id + module_id + stratum_id` keys.
13. Confirm that every structural row has one final technical/scientific
   status, including untestable rows.
14. Confirm donor/context keys are unique and `projid` remains a character ID.
15. Confirm that the 13-gene mtDNA and 86-gene nuclear OXPHOS memberships match
    the frozen config exactly.
16. Independently recompute BH q values from saved finite P values for the
    complete 196-row module-score family and separately for the complete
    196-row `camera` family; compare with stored q values without refitting.
17. Reproduce donor-count, module-coverage, estimate/SE/CI, and gate-component
    fields from saved inputs under frozen tolerances.
18. Confirm that no result table was manually edited after publication.
19. Save an output-only validation report outside the Phase 13 directory.

**Outputs**

```text
results/<version>/post_phase13_review/phase13_input_inventory.tsv
results/<version>/post_phase13_review/phase13_output_validation.tsv
results/<version>/post_phase13_review/phase13_dependency_status.tsv
```

**Ready when**

Every required file, key, dimension, schema, and hash passes independently.

**Stop condition**

If any blocking validation fails, do not open scientific effect estimates for
downstream selection. Repair or rerun Phase 13 under its own contract.

### H.2 Task 2: lock and explain the complete C1 result

**Question answered**

What exactly did Phase 13 support, and what did it not support?

**Why this is necessary**

The strongest-looking estimate is not automatically the result. The result is
determined by the prespecified gate, uncertainty, donor counts, and stability.

**Inputs**

- `respiratory_claim_summary.tsv`;
- `respiratory_gate_decisions.tsv`;
- `respiratory_module_results.tsv`;
- `respiratory_module_stratum_effects.tsv`;
- `respiratory_camera_results.tsv`;
- `respiratory_stability_summary.tsv`; and
- donor/module reliability and coverage tables.

**Exactly what to do**

1. Read the overall C1 label from the saved claim summary.
2. Independently recompute the sex, APOE, and overall C1 labels from the 196
   gate rows under the frozen Phase 13 rules and compare them with the saved
   claim summary. In particular, confirm that inconclusive rows are not
   mislabeled `not_supported` and that an empty set of internally confirmable
   rows cannot create a precise-null conclusion.
3. If the recomputed label disagrees, stop the wording review. Record the
   discrepancy and correct/version the Phase 13 implementation rather than
   silently editing a published summary.
4. Preserve all 196 rows in their frozen order.
5. For every row, record:
   - context;
   - exact sex/APOE contrast;
   - module;
   - estimate and sign;
   - 95% CI;
   - raw P value and family-wide q value;
   - four required donor counts;
   - module coverage;
   - `camera` direction and q value;
   - bootstrap sign fraction;
   - leave-one-donor-out reversals;
   - PC1, 50-nucleus, balance, QC, and omission results; and
   - final status and permitted wording.
6. Verify every direct modifier estimate against the correct pair of adjusted
   stratum AD effects using `context_id + module_id + stratum_id` and the
   coefficient rule in the contrast manifest.
7. Separate the two direct respiratory modules from the two supporting
   programs:

   ```text
   direct respiratory:
       mtdna_oxphos_13
       nuclear_oxphos_structural_86

   supporting programs:
       mitochondrial_translation_155
       mib_micos_inner_membrane_19
   ```

8. Do not let a translation- or membrane-only result change the overall C1
   respiratory label.
9. Mark e2 results with 5-9 donors in a required group as provisional even if
   their estimated effects are large.
10. Write one allowed sentence for every supported row.
11. Write one limitation sentence for every provisional, inconclusive, or
   untestable row considered biologically important.
12. For inconclusive rows, report CI width, overlap with the `[-0.25,+0.25]`
    meaningful-effect range, donor counts, and the failed stability component.
    Do not calculate observed/post-hoc power from the observed effect.
13. If future sample-size planning is needed, use a prospective calculation
    based on a separately frozen target effect.
14. Lock the table and wording before reviewing C2-C9 results.

**Outputs**

```text
results/<version>/post_phase13_review/c1_locked_evidence_matrix.tsv
results/<version>/post_phase13_review/c1_supported_rows.tsv
results/<version>/post_phase13_review/c1_provisional_and_limitation_rows.tsv
results/<version>/post_phase13_review/c1_allowed_wording.md
```

**Decision rule**

Use the status already produced by the Phase 13 gate. A post-completion review
may explain it but must not invent a new threshold or upgrade a row by visual
judgment.

**What this task cannot prove**

It cannot establish C2, C3, candidate regulation, mitochondrial function,
causality, or external replication.

### H.3 Task 3: create the Phase 13 evidence figure package

**Question answered**

Can readers see the C1 estimate, uncertainty, component group effects, and
stability without reconstructing the analysis from prose?

**Why this is necessary**

A q value alone does not show effect size, donor imbalance, or whether one
donor drives the result.

**Inputs**

- locked C1 evidence table;
- `respiratory_donor_module_scores.tsv.gz`;
- `respiratory_donor_samples.tsv.gz`;
- module and gene result tables;
- module membership and admitted-gene coverage tables; and
- stability replicate/summary tables.

Before plotting donor points, join scores one-to-one with donor samples using:

```text
context_id + projid
```

Verify diagnosis, sex, APOE, and group labels agree. The score table alone does
not contain every required age, PMI, study, nucleus-count, or QC field.

**Exactly what to do**

1. Build a signed overview heatmap:
   - rows = seven broad contexts;
   - columns = seven direct modifiers;
   - one panel = one module;
   - color = signed standardized estimate;
   - symbol/outline = final gate status;
   - adjacent annotation or plotted-data fields = CI, q, and donor counts.
     Static SVG/PDF/PNG files do not have reliable tooltips.
2. Build the primary direct-respiratory forest using all 98 rows:

   ```text
   7 contexts × 7 modifiers × 2 direct respiratory modules = 98
   ```

   - show every estimate and 95% CI;
   - include the zero line and the ±0.25 project threshold;
   - show q value and four donor counts;
   - keep provisional and inconclusive rows visible.
3. Build detailed explanation pages for every `supported`,
   `provisional_low_power`, or `statistically_detectable_but_small` row in
   frozen order. Do not choose pages by largest effect.
4. For each detailed interaction panel:
   - plot donor scores by AD/NCI, sex, and APOE;
   - show the six adjusted within-stratum AD effects;
   - label the direct difference-of-differences as the tested result.
5. Build a robustness panel using row-specific stability fields:
   - bootstrap distribution;
   - leave-one-donor-out range and influential donor;
   - 20- versus 50-nucleus comparison;
   - mean-z versus PC1 comparison;
   - balanced-group and QC/omission status.
6. For gene panels, join gene interaction rows by
   `assay_feature_identifier` to the frozen module membership and admitted-gene
   tables. Show every admitted member, not only significant DEGs.
7. Order gene panels by frozen respiratory complex or functional category.
8. Never use a single-gene volcano plot as the evidence that C1 passed.
9. Preserve full donor identifiers only in restricted internal source data;
   anonymize publication-facing labels.
10. Provide a plotted-data table, caption, methods note, manifest, checks, and
    status for every figure family.

**Outputs**

Recommended root:

```text
results/figures/phase13_respiratory_modifier/
```

Recommended files:

```text
phase13_c1_review_summary.tsv
phase13_c1_selected_detail_rows.tsv
phase13_c1_landscape_plotted_data.tsv
phase13_c1_forest_plotted_data.tsv
phase13_c1_row_explanation_plotted_data.tsv.gz
phase13_c1_stability_plotted_data.tsv.gz
phase13_c1_gene_support_plotted_data.tsv.gz
phase13_c1_testability_plotted_data.tsv
phase13_c1_landscape.svg
phase13_c1_landscape.pdf
phase13_c1_landscape.png
phase13_c1_direct_respiratory_forest.svg
phase13_c1_direct_respiratory_forest.pdf
phase13_c1_direct_respiratory_forest.png
phase13_c1_row_explanations.pdf
phase13_c1_stability_atlas.pdf
phase13_c1_gene_support_atlas.pdf
phase13_c1_testability_qc.svg
phase13_c1_testability_qc.pdf
phase13_c1_testability_qc.png
phase13_c1_figure_captions.md
phase13_c1_figure_methods.md
phase13_c1_figure_manifest.tsv
phase13_c1_figure_checks.tsv
phase13_c1_figure_status.tsv
```

Each plotted-data row must include, where relevant, `panel_id`, `record_type`,
`test_id`, source file/path, source hash, and analysis fingerprint.

**Ready when**

Every plotted number traces to a validated Phase 13 row and the figure does not
change the analysis population, q values, or gate status.

**What this task cannot prove**

An attractive figure is communication, not a new independent analysis.

### H.4 Task 4: choose the branch from the locked C1 outcome

Use the following decision table without searching for a more favorable result.

| Locked C1 outcome | Meaning | Required action | Prohibited response |
|---|---|---|---|
| `supported_both` | At least one sex and one APOE direct-respiratory row passed | Freeze exact rows; prioritize Phase 14, Phase 15, matching candidate tests, then external replication | Generalize to all sexes, APOE groups, modules, or contexts |
| `supported_sex_only` | A sex modifier passed but no APOE modifier passed | Retain only the exact sex clause; APOE remains unsupported | Write a combined sex/APOE claim |
| `supported_apoe_only` | An APOE modifier passed but no sex modifier passed | Retain only the exact APOE clause; sex remains unsupported | Write a combined sex/APOE claim |
| `provisional_low_power` row | Pattern passed non-count rules but a required group had 5-9 donors | Report effect, CI, counts, and instability; seek more donors/direct frozen replication | Use it as a confirmatory headline or C7 authorization by itself |
| `inconclusive` | CI or stability cannot decide | Identify the exact cause; complete missing technical checks or seek a larger independent frozen test | Search new modules until one is significant |
| `not_supported` | Internally confirmable direct-respiratory rows are precise nulls | Remove the C1 modifier clause; keep only separately supported narrower results | Let candidates or KDA rescue C1 |
| `not_testable` | Required data/design were insufficient | Repair the data/design limitation before interpretation | Treat missing evidence as a negative biological result |

Important branch rules:

- Phase 15 still runs after a negative or inconclusive C1 because C3 is a
  different biological question.
- Phase 14 can run technically after validated Phase 13, but a supported C2
  pair requires at least one matching supported Phase 13 context row.
- C4-C6 may be estimated as separate targeted hypotheses, but cannot rescue a
  failed core claim.
- C7 does not start merely because the Phase 12 KDA nominated a candidate.

**Output**

```text
results/<version>/post_phase13_review/post_phase13_branch_decision.tsv
```

Required fields include:

```text
c1_overall_status
supported_sex_rows
supported_apoe_rows
provisional_rows
phase14_technically_allowed
phase15_technically_allowed
candidate_tests_allowed
c7_currently_authorized
external_replication_target
permitted_claim
reviewer
review_date
analysis_fingerprint
```

### H.5 Task 5: run Phase 14 to test Claim 2

**Question answered**

Does a Phase 13 sex/APOE modifier differ directly between two broad cell
contexts?

**Why this is necessary**

This pattern is not enough:

```text
astrocytes: significant
excitatory neurons: not significant
```

Different P values can result from different donor counts or uncertainty.
Phase 14 directly tests the difference between the two modifier estimates.

**Current implementation status**

- Phase 14 config, script, and tests exist.
- Its deterministic synthetic local pilot was executed.
- Minerva production remains unapproved and has no production bundle.
- Production cannot start until validated Phase 13 exists and Phase 14
  production is approved.

**Inputs**

- validated Phase 13 status, checks, artifacts, and manifests;
- donor/context raw counts and expression bundle;
- Phase 13 module scores and NCI reference parameters;
- donor metadata and context overlap;
- four frozen module definitions; and
- seven frozen modifier definitions.

**Exactly what Phase 14 does**

1. Intersect admitted genes so each compared context uses a comparable module
   definition.
2. Recalculate common-gene donor module scores.
3. Preserve repeated donors across contexts.
4. Fit one joint repeated-donor mixed model for each module.
5. Test 28 global heterogeneity questions:

   ```text
   7 modifiers × 4 modules = 28 omnibus tests
   ```

6. Test 588 direct context-pair questions:

   ```text
   7 modifiers × 4 modules × 21 unordered context pairs = 588
   ```

7. Correct the omnibus and pairwise testing families separately.
8. Require a direct pairwise effect and CI; do not compare Phase 13
   significance labels.
9. Run donor bootstrap, leave-one-donor-out, pair-complete, 50-nucleus,
   balanced-group, PC1, QC, and score sensitivities.
10. Preserve every negative, provisional, and untestable row.

**A Phase 14 pair is supported only when**

- its parent omnibus q value is at most 0.05;
- the direct pairwise family-wide q value is at most 0.05;
- the absolute context-difference estimate is at least 0.25 and its CI excludes
  zero;
- at least one matching Phase 13 context row is supported for the same
  modifier and module;
- the common-score context effects agree with the carried Phase 13 result;
- every required paired group has at least 10 donors; and
- every mandatory stability and technical check passes.

**Key outputs**

```text
results/minerva_production/14_modifier_heterogeneity/
    heterogeneity_context_modifier_effects.tsv
    heterogeneity_omnibus_results.tsv
    heterogeneity_pairwise_results.tsv
    heterogeneity_pairwise_stability_summary.tsv
    heterogeneity_gate_decisions.tsv
    heterogeneity_claim_summary.tsv
    heterogeneity_status.tsv
```

**Allowed wording after a supported pair**

> In ROSMAP donor-level profiles, the [exact sex/APOE] modification of the
> AD-associated [exact module] expression effect differed between [context 1]
> and [context 2].

**What Phase 14 cannot prove**

- that every fine subtype inside the broad context behaves the same;
- that the effect is unique to one context unless all claimed comparisons were
  directly tested;
- mitonuclear coupling;
- candidate regulation; or
- independent replication.

Full contract: [Phase 14 modifier heterogeneity plan](../phase_14_modifier_hetrogeneity/phase_14_modifier_heterogeneity_plan.md).

### H.6 Task 6: run Phase 15 to test Claim 3

**Question answered**

Does AD alter the RNA-expression relationship between the 13 mtDNA respiratory
genes and the 86 nuclear OXPHOS structural genes, and does that alteration
differ by sex or APOE?

**Why this is necessary**

Phase 13 tests each program's abundance. It does not formally test the
relationship between the two compartments.

**Critical dependency rule**

Phase 15 requires technically validated Phase 13. It does **not** require a
positive C1 result and does **not** depend on Phase 14. It must analyze all
eligible frozen contexts rather than selecting positive Phase 13 rows.

**Current implementation status**

- the Phase 15 scientific/execution plan, config, script, and tests exist;
- its plan records a successful synthetic local pilot on 2026-08-09;
- Minerva production remains unapproved; and
- no Phase 15 Minerva production bundle exists.

**Inputs**

- the exact 13- and 86-gene Phase 13 memberships;
- paired donor mtDNA and nuclear OXPHOS scores;
- broad donor counts and expression bundle;
- NCI reference parameters and PC1 loadings;
- diagnosis, recorded sex, APOE, age, PMI, study, nucleus count, and QC; and
- Phase 13 status/check/artifact manifests.

**The three endpoints**

1. **Standardized compartment difference**

   ```text
   D = mtDNA score - nuclear OXPHOS score
   ```

   This asks whether one standardized compartment is relatively higher or
   lower than the other.

2. **Cross-fitted NCI-reference residual**

   ```text
   residual = observed mtDNA score - mtDNA score predicted from the
              NCI mtDNA-nuclear relationship
   ```

   Cross-fitting prevents an NCI donor from helping fit the relationship used
   to predict that same donor.

3. **Coupling-slope change**

   This directly tests whether the mtDNA-versus-nuclear expression slope
   changes. It does not compare “significant correlation” with “nonsignificant
   correlation.”

**Planned families**

Primary neural contexts are astrocytes, excitatory neurons, and inhibitory
neurons:

```text
general C3:   3 endpoints × 3 contexts = 9 primary tests
modifier C3:  3 endpoints × 7 modifiers × 3 contexts = 63 primary tests
```

Immune cells, OPCs, oligodendrocytes, and vasculature form separate secondary
families:

```text
secondary general:   3 × 4 = 12
secondary modifier:  3 × 7 × 4 = 84
```

**A C3 gate is supported only when**

- at least two of three endpoints pass their frozen effect, CI, q-value,
  eligibility, and stability rules;
- at least one carrying endpoint is the NCI residual or slope;
- their biological directions are compatible under the frozen rule;
- module coverage and reliability pass;
- the required donor/reference counts pass; and
- bootstrap, leave-one-donor-out, 50-nucleus, PC1, normalization, QC,
  gene/complex influence, reference, and slope-specific checks pass.

**Residual bridge authorization**

The full cross-fitted 13-versus-86 residual is the planned shared candidate
convergence outcome. Set `bridge_authorized = TRUE` only when:

- the matching general or modifier C3 gate passes;
- the residual endpoint itself is supported for that exact context and
  comparison;
- all residual-reference sensitivities pass; and
- the endpoint definition remains frozen.

C3 can pass using the difference and slope while the residual fails. In that
case, C3 wording may be permitted, but the residual is not authorized as the
candidate bridge.

**Key outputs**

```text
results/minerva_production/15_mitonuclear_coupling/
    mitonuclear_donor_endpoints.tsv.gz
    mitonuclear_general_results.tsv
    mitonuclear_modifier_results.tsv
    mitonuclear_group_slopes.tsv
    mitonuclear_prediction_grid.tsv.gz
    mitonuclear_general_stability_summary.tsv
    mitonuclear_modifier_stability_summary.tsv
    mitonuclear_general_gate_decisions.tsv
    mitonuclear_modifier_gate_decisions.tsv
    mitonuclear_claim_summary.tsv
    mitonuclear_status.tsv
```

**What Phase 15 cannot prove**

- oxygen consumption or ATP production;
- mtDNA copy-number change;
- protein-level coordination;
- candidate regulation;
- causality; or
- cell-context specificity without a direct between-context C3 analysis.

Full contract: [Phase 15 mitonuclear coupling plan](../phase_15_mitonuclear_coupling/phase_15_mitonuclear_coupling_plan.md).

### H.7 Task 7: test C4, C5, and C6 donor-level candidate phenotypes

**Question answered**

Does each network-nominated candidate system have its predicted named readout
and local expression program in the correct donor group and cell context?

**Why this is necessary**

Network analysis can nominate a gene because it is a highly connected hub or
because the query contains nearby genes. Before expensive network simulations,
the candidate's predicted biological readout should be visible at the donor
level.

**Important boundary**

Phase 13 does not test C4-C6. It contains mitochondrial translation, but it
does not contain all required target-excluded candidate scores. In particular,
ATP-synthase and mitophagy candidate modules require a new frozen candidate
manifest and workflow.

**The three independent candidate hypotheses**

| Claim | Candidate system | Broad primary context | Fine localization, if eligible | Required named readout | Proposed target-excluded local program | Required companion result |
|---|---|---|---|---|---|---|
| C4 | `APOE–TUFM` | Astrocytes | `Ast GRM3` | `TUFM` | Mitochondrial translation excluding `TUFM` | Nuclear OXPHOS and, for convergence wording, an authorized C3 bridge |
| C5 | `LAMTOR5–ATP5IF1` | Excitatory neurons; inhibitory secondary | Frozen `Exc L2-3 CBLN2 LINC02306` and `Exc L3-4 RORB CUX2` contexts | `ATP5IF1` | ATP synthase/Complex V excluding `ATP5IF1` | Nuclear OXPHOS and, for convergence wording, an authorized C3 bridge |
| C6 | `GABARAPL2–CHCHD2/PARK7` | Excitatory neurons | The same frozen eligible excitatory contexts | `CHCHD2` primary; `PARK7` secondary | A frozen mitochondrial maintenance program that cannot reuse its named readouts | Respiratory result and, for convergence wording, an authorized C3 bridge |

`APOE group` and the `APOE` gene must not be confused:

- APOE group is the donor's inherited e2/e33/e4 genotype category.
- `APOE` in `APOE–TUFM` is the measured APOE gene/network node.

They are related biological concepts but are not the same model variable.

#### Blocking C6 definition that must be resolved

Two local documents currently describe different C6 programs:

- the deep-dive plan uses a broad quality-control score excluding `CHCHD2`
  and `PARK7`;
- the newer module guide recommends the MitoCarta mitophagy set of 14 genes,
  excluding `PARK7` to leave 13 genes, while testing `CHCHD2` separately.

The newer mitophagy definition is more concrete, but it is not automatically
approved. Before C6 outcome testing:

1. choose one primary C6 program;
2. write its exact gene list and identifiers;
3. state why it measures the proposed local biology;
4. remove the named readout where present;
5. audit overlap with the shared respiratory endpoint; and
6. freeze its multiplicity family and coverage rules.

Do not run both definitions and select the one with the smaller q value.

#### Recommended candidate-module definitions to approve

| Candidate | Source definition | Reference size | Primary target-excluded score | Sensitivity |
|---|---|---:|---|---|
| C4 | Phase 13 MitoCarta translation module | 155 | 154 genes after removing `TUFM`, if all are admitted | Translation child-category and gene-omission checks |
| C5 | MitoCarta Complex V subunit/regulator set | 21 | Prefer the 18 nuclear structural genes; `ATP5IF1` is absent | All 20 non-`ATP5IF1` Complex V genes, including 2 mtDNA genes |
| C6 | Proposed MitoCarta mitophagy set | 14 | 13 genes after removing `PARK7`; `CHCHD2` remains a separately tested primary readout | A separately approved broader quality-control score, never selected post hoc |

All measured/admitted counts must be recalculated in each context. Reference
size is not the same as usable score size.

**Inputs**

- Phase 13 donor pseudobulk counts and normalized expression;
- Phase 13 gene and module results;
- frozen candidate/context/contrast/direction manifest;
- exact target-excluded module membership manifest;
- Phase 14 results when between-context wording is intended;
- Phase 15 results when mitonuclear or convergence wording is intended; and
- donor counts, covariates, study, and QC data.

**Exactly what to do for each candidate**

1. Freeze the candidate system, exact comparison, expected direction, broad
   context, optional fine context, named readout, and local program.
2. Count eligible donors and admitted genes before viewing the candidate
   effects.
3. Fit the same direct donor-level modifier contrast used in Phase 13.
4. Report the candidate gene's expression as descriptive/supportive. The
   candidate itself does not have to be a DEG.
5. Test the required named readout and its CI.
6. Calculate the target-excluded local-program score.
7. Test the local-program direct modifier and CI.
8. Report the companion respiratory result separately.
9. Estimate candidate-readout and candidate-local-program associations after
   accounting for the frozen biological groups, age, PMI, study, library/QC
   information, and donor structure.
10. Test group-dependent coherence only as prespecified supporting evidence.
11. Add Phase 14 evidence only when a formal context-difference claim is made.
12. Add Phase 15 evidence only when the matching C3 row was tested.
13. Run donor bootstrap, leave-one-donor-out, balance, 50-nucleus, alternative
   score, QC, and gene-omission sensitivities.
14. Assign Gate 3A, 3B, or 3C independently.

#### Non-circular bridge requirement for convergence

An authorized C3 residual does not automatically connect a candidate to C3.
This bridge is a proposed strengthening of the candidate evidence chain; it is
not a Phase 13 output and is not fully specified in the current simplified
Gate 3 table. Before candidate execution, add the exact bridge model,
multiplicity family, pass rule, and output schema to the authoritative
candidate plan so all documents use one definition.

For each candidate:

1. choose a scientifically meaningful candidate/upstream donor measurement;
2. confirm that it does not simply reuse the respiratory endpoint genes;
3. audit and save all overlap;
4. if overlap remains, construct and freeze a defensible overlap-depleted
   sensitivity before outcome testing;
5. test its adjusted donor-level association with the unchanged authorized C3
   residual in the exact context/comparison; and
6. report `not_testable` when no valid nonoverlapping measurement remains.

The local target-excluded phenotype and the non-circular C3 bridge are two
different pieces of evidence. Neither substitutes for the other.

**Candidate phenotype gate**

A candidate may proceed to C7 only when all required conditions pass:

- its target-excluded local program has q at most 0.05;
- the program meets the frozen meaningful-effect and CI rule;
- the required named readout has a compatible effect under the frozen
  candidate-gene family rule;
- the exact context and modifier match the hypothesis;
- donor counts meet the confirmation rule, or the row remains provisional;
- every mandatory donor/QC/score stability check passes; and
- the candidate-specific decision row is approved.

For C6, `CHCHD2` is primary. `PARK7` cannot rescue an unsupported `CHCHD2`
result.

**Outputs**

```text
results/<version>/candidates/candidate_analysis_manifest.tsv
results/<version>/candidates/candidate_module_members.tsv
results/<version>/candidates/candidate_eligibility.tsv
results/<version>/candidates/candidate_gene_effects.tsv
results/<version>/candidates/candidate_module_effects.tsv
results/<version>/candidates/candidate_context_results.tsv
results/<version>/candidates/candidate_mediator_coherence.tsv
results/<version>/candidates/candidate_common_endpoint_results.tsv
results/<version>/candidates/candidate_stability_summary.tsv
results/<version>/candidates/candidate_gate_decisions.tsv
results/<version>/candidates/round2_authorization_manifest.tsv
```

**What this task cannot prove**

- that the candidate regulates the named readout;
- that the candidate causes the local program;
- mediation or molecular direction;
- physical interaction;
- altered mitochondrial function; or
- convergence unless the core endpoint, bridge, candidate phenotype, and
  later C7 gate all pass.

### H.8 Task 8: perform focused fine-cell localization

**Question answered**

Which prespecified fine subtype may localize a supported broad-context result?

**When this is allowed**

Fine localization is allowed when:

- a broad Phase 13 result is supported and needs localization; or
- the candidate fine context was frozen before candidate outcome testing and
  passed eligibility.

It is not an unrestricted all-54-cell discovery screen.

**Inputs**

- validated Phase 07 fine-context pseudobulk counts;
- donor/context eligibility and metadata;
- frozen broad result;
- small fine-type manifest;
- exact contrast and module; and
- separate fine-type multiplicity family.

**Exactly what to do**

1. Freeze the eligible fine contexts before viewing their new effects.
2. Preserve one donor profile per fine context.
3. Require the same four diagnosis/group cells for a direct modifier.
4. Use donor-level count models and module scores.
5. Test the exact direct modifier, not separate group significance.
6. Report donor counts and precision for every fine context.
7. Correct the entire frozen fine-context family.
8. Run bootstrap, leave-one-donor-out, 20/50-nucleus, alternative-score, and QC
   checks where estimable.
9. Compare a fine context with another nonoverlapping context directly before
   using fine-type-specific wording.

**Outputs**

```text
results/<version>/fine_localization/fine_context_manifest.tsv
results/<version>/fine_localization/fine_eligibility.tsv
results/<version>/fine_localization/fine_module_results.tsv
results/<version>/fine_localization/fine_gene_results.tsv.gz
results/<version>/fine_localization/fine_stability_summary.tsv
results/<version>/fine_localization/fine_localization_summary.tsv
```

**What this task cannot prove**

A fine-type result cannot rescue a failed broad primary result. Significance in
one fine type and nonsignificance in another does not prove that their effects
differ.

### H.9 Task 9: hold the locked C1-C6 review

**Question answered**

Which claim clauses and candidate rows have earned permission to advance?

**Why this is necessary**

Looking at C1-C6 together before C7 prevents network results from redefining
the biological phenotype they are supposed to explain.

**Exactly what to do**

1. Load saved results rather than copying numbers from figures.
2. Update separate evidence rows for:
   - C1 respiratory modifier;
   - C2 context heterogeneity;
   - C3 general and modifier mitonuclear outcomes;
   - C4 `APOE–TUFM` phenotype;
   - C5 `LAMTOR5–ATP5IF1` phenotype; and
   - C6 `GABARAPL2–CHCHD2/PARK7` phenotype.
3. Preserve `supported`, `provisional`, `partial`, `inconclusive`, precise-null,
   and not-testable distinctions.
4. Record whether Phase 15 set `bridge_authorized = TRUE` for each exact
   context/comparison.
5. Record whether each candidate passed its non-circular bridge test.
6. List candidate rows authorized for C7.
7. Freeze the shared endpoint and candidate definitions for any later
   convergence claim.
8. Write the exact allowed and forbidden sentences.

**Outputs**

```text
results/<version>/post_phase13_review/c1_to_c6_evidence_matrix.tsv
results/<version>/post_phase13_review/c1_to_c6_claim_summary.md
results/<version>/post_phase13_review/bridge_authorization.tsv
results/<version>/candidates/round2_authorization_manifest.tsv
```

**Decision rules**

- A failed candidate removes only that candidate.
- C2 failure removes context-specific wording but does not automatically erase
  a supported C1 row.
- C3 failure removes mitonuclear wording but does not automatically erase a
  supported C1 abundance result.
- Candidate success cannot rescue failed C1 or C3 clauses.
- If only two candidates ultimately pass, the final sentence must name two,
  not three.

### H.10 Task 10: run C7 network validation only for authorized candidates

**Question answered**

Does a surviving network candidate remain unusual after controlling for query
composition, network connectedness, layer selection, and network instability?

**Terms used in this task**

- **Query-matched null:** a random gene list resembling the observed query in
  size, expression, detection, mitochondrial composition, and network-degree
  properties.
- **Topology-matched null:** candidate genes or rewired networks having similar
  connectedness, neighborhood size, and tested coverage.
- **Self-excluded KDA:** query genes are removed from the possible driver list,
  preventing a query gene from nominating itself.
- **Network perturbation:** slightly change network links and repeat the
  ranking to determine whether the result is stable.
- **Alternative donor network:** a second network built from donor-level
  coexpression rather than treating individual nuclei as independent samples.

**Inputs**

- only rows in `round2_authorization_manifest.tsv`;
- donor-supported directional query signatures;
- cell-matched Bayesian networks;
- exact tested-gene/network backgrounds;
- complete KDA results, including null candidates;
- frozen layers, null rules, seeds, and candidate family; and
- donor pseudobulk expression for an alternative network.

**Exactly what to do**

1. Use only frozen primary directional signatures.
2. Require at least 10 effective query genes.
3. Remove every effective query gene from the possible driver list.
4. Exclude mtDNA structural genes as candidate drivers.
5. Test layers 1, 2, and 3 separately.
6. Correct for candidate-by-layer selection.
7. Save every tested candidate and null result.
8. Generate at least 1,000 query-matched null lists.
9. Generate at least 1,000 topology-matched candidate/network nulls.
10. Perturb edges and rerun candidate ranking.
11. Build one bootstrap-preserved broad-context donor coexpression network.
12. Test whether the candidate and named readout share a preserved module or
    are closer than degree-matched chance.
13. Remove query genes and the shared respiratory core, then test whether the
    proposed systems retain distinguishable local neighborhoods.

**Candidate-specific Gate 4**

Every required condition must pass for each candidate separately:

- corrected KDA q at most 0.05;
- empirical q at most 0.05 under both null families;
- observed evidence above the 95th null percentile;
- top-decile rank in at least 80% of network perturbations;
- alternative-network proximity or module support at q at most 0.05; and
- alternative-network support preserved in at least 80% of donor bootstraps.

**Outputs**

```text
results/<version>/kda/kda_fixed_layer_complete.tsv.gz
results/<version>/kda/kda_query_nulls.tsv.gz
results/<version>/kda/kda_topology_nulls.tsv.gz
results/<version>/kda/network_perturbation_results.tsv.gz
results/<version>/networks/alternative_network_support.tsv
results/<version>/networks/candidate_distinctness.tsv
results/<version>/kda/robust_driver_summary.tsv
```

**Allowed wording after a pass**

> [Candidate] is a robust network-nominated system associated with the frozen
> donor-level mitochondrial endpoint in [exact context/comparison].

**What C7 cannot prove**

- activation or inhibition;
- physical binding;
- molecular direction;
- mediation; or
- causality.

If C7 fails, the donor-level phenotype can remain supported, but the candidate
must be described as hypothesis-generating rather than a robust network
candidate.

### H.11 Task 11: run C8 independent RNA replication

**Question answered**

Does a frozen respiratory, mitonuclear, or surviving candidate result appear in
a different set of donors?

**Important dependency rule**

C8 does not require C7 when replicating the core C1 or C3 biological result.
Candidate-specific replication should be limited to candidates that passed the
appropriate donor phenotype gate and, when the network claim is being
replicated, C7.

**Required external information**

- donor identifiers independent of ROSMAP;
- compatible AD/comparison definitions;
- recorded sex;
- APOE genotype if the modifier itself will be replicated;
- adequate donors in all required groups;
- suitable broad-cell coverage and a frozen taxonomy mapping;
- required module/candidate gene coverage;
- relevant covariates and study/batch information; and
- enough raw or summary information to estimate the frozen effect and CI.

**Exactly what to do**

1. Freeze the ROSMAP result, direction, genes, context mapping, and contrast
   before viewing external effects.
2. Write the external feasibility report before testing outcomes.
3. Map broad cell contexts using a documented rule fixed before effects.
4. Build one donor-level profile per mapped cell context when raw counts are
   available.
5. Recalculate the frozen module or C3 endpoint without searching for a better
   pathway.
6. Fit the closest valid direct contrast supported by the external design.
7. Test the sex/APOE modifier only if every required external group is
   adequately represented.
8. Test candidate/readout coherence only for surviving candidates.
9. Display standardized discovery and validation effects with CIs.
10. Document differences in brain region, diagnosis/pathology, sequencing,
    covariates, and cell taxonomy.
11. Preserve `not_testable` when the exact modifier cannot be estimated.
12. Do not replace a failed frozen result with an externally discovered one.

**Gate 5A**

The frozen expression result is independently replicated only when:

- the effect direction agrees; and
- the validation q value is at most 0.05, or a separately frozen meta-analysis
  decision rule passes.

If sex/APOE metadata or group counts are inadequate, the external resource may
replicate the broad respiratory/mitonuclear program but cannot replicate the
modifier.

**Outputs**

```text
results/<version>/validation/external_rna_feasibility.tsv
results/<version>/validation/external_context_mapping.tsv
results/<version>/validation/external_rna_eligibility.tsv
results/<version>/validation/external_rna_replication.tsv
results/<version>/validation/external_rna_claim_summary.tsv
```

**What C8 cannot prove**

- causality;
- protein change;
- mitochondrial function; or
- universal generalization across brain regions and disease definitions.

If C8 fails, use “internally supported in ROSMAP,” not “replicated.”

### H.12 Task 12: run C9 protein support

**Question answered**

Does a frozen RNA program, candidate, or named readout receive support from
protein abundance?

**Why this is useful**

RNA abundance is not the same as protein abundance. Protein evidence tests the
same biological idea using a different measurement type.

**Inputs**

- a frozen surviving RNA result;
- protein-level donor identifiers and diagnosis/metadata;
- measured-protein coverage;
- information about donor overlap with ROSMAP; and
- sufficient group sizes for any planned modifier.

MSBB and BLSA are conditional independent protein-resource directions named in
the project plan. Their access, donor independence, tissue relevance, metadata,
and protein coverage must be verified. ROSMAP proteomics from overlapping
donors is same-cohort orthogonal support, not independent replication.

**Exactly what to do**

1. Freeze the RNA targets before opening protein results.
2. Report coverage before performing significance tests.
3. Label an absent protein `not_measured`, not failed.
4. Test only frozen modules, candidates, and named readouts.
5. Compare standardized protein direction and uncertainty with RNA evidence.
6. Test sex/APOE interactions only when all required protein groups are
   adequately represented.
7. Separate:
   - independent-cohort protein support;
   - same-cohort orthogonal protein support;
   - measured but unsupported; and
   - not measured.
8. Do not require every RNA gene and protein to have identical effects.

**Gate 5B**

Protein support requires a directionally concordant frozen module, candidate,
or readout result with q at most 0.05 under its frozen protein family.

**Outputs**

```text
results/<version>/validation/protein_coverage.tsv
results/<version>/validation/protein_validation.tsv
results/<version>/validation/protein_claim_summary.tsv
```

**What C9 cannot prove**

- causality;
- mitochondrial respiratory function;
- independent replication when donors overlap; or
- that RNA and protein must agree gene by gene.

### H.13 Task 13: consider optional extensions only after the core review

#### H.13.1 Mitochondrial-selectivity analysis

Run this only if the intended sentence says mitochondrial changes are
selective, stronger, or more profound than other transcriptomic changes.

Construct at least 1,000 nonmitochondrial gene sets matched on:

- gene-set size;
- expression;
- detection;
- gene length;
- tested coverage; and
- relevant network-degree properties when used with a network result.

Compare the frozen mitochondrial effect with the empirical matched-null
distribution. `camera` provides transcriptome-relative context but is not an
expression/detection-matched selectivity null.

#### H.13.2 Secondary mitochondrial programs

The following can be prespecified as a later secondary panel:

| Program | Reference size in the local MitoCarta source | Narrow interpretation |
|---|---:|---|
| OXPHOS assembly factors | 68 | Respiratory-complex assembly/maintenance expression |
| ROS and glutathione metabolism | 27 | Mitochondrial oxidative-stress defense expression |
| Protein import and sorting | 48 | Mitochondrial protein transport expression |
| Mitochondrial chaperones | 16 | Mitochondrial protein-folding/stress expression |
| MIB/MICOS and inner-membrane organization | 19, with an overlap-depleted sensitivity | Inner-membrane/cristae organization expression |

Requirements:

1. use a curated versioned source;
2. write exact genes before testing;
3. report overlap with the four Phase 13 and candidate modules;
4. freeze one complete secondary FDR family;
5. preserve all negative rows; and
6. require independent confirmation before promoting a discovered program.

Secondary modules can extend a supported story. They cannot rescue failed
C1-C7 gates.

#### H.13.3 Pathology, cognition, and resilience

These questions are biologically valuable but are not required to validate the
current central claim. Treat them as a separate follow-up plan with:

- one donor as the sample;
- explicitly defined pathology/cognition outcomes;
- donor-level module scores;
- frozen covariates and subgroup logic;
- continuous outcomes as primary when appropriate;
- separate multiple-testing families; and
- clear separation from the C1-C9 gates.

Do not start this branch merely to compensate for a failed respiratory
modifier.

#### H.13.4 Perturbation and rescue for causal wording

Only the strongest externally or orthogonally supported survivors should enter
functional testing.

Minimum design elements include:

- a cell-context-relevant model;
- preferably isogenic background;
- candidate loss-of-function and/or gain-of-function;
- rescue that restores the candidate or predicted pathway;
- biological replicates;
- randomization and blinded outcome assessment where practical;
- cell-health and toxicity controls;
- named readout and target-excluded program measurements; and
- direct mitochondrial measurements such as oxygen-consumption or ATP-related
  assays when those functions are claimed.

Only successful perturbation plus rescue can begin to support words such as
“regulates,” “mediates,” or “drives.”

### H.14 Task 14: freeze the final claim and evidence package

**Question answered**

What is the strongest sentence supported by all completed evidence, and which
parts remain provisional or failed?

**Exactly what to do**

1. Update the claim-to-evidence matrix using saved outputs only.
2. Name the exact number of candidate systems passing every required gate.
3. Keep core biological, candidate, network, replication, protein, and causal
   evidence in separate columns.
4. Label same-cohort and independent evidence separately.
5. Distinguish `not_measured` from `tested_unsupported`.
6. Write one allowed sentence and one limitation sentence per surviving claim.
7. Preserve failed/inconclusive rows in a supplement or audit table.
8. Freeze all figure source-data tables before manuscript wording is finalized.

**Counting candidate convergence**

- Three candidates pass: say three candidate systems converge.
- Two pass: name the two; do not keep the third for narrative symmetry.
- One passes: name one robust candidate; do not say multiple systems converge.
- None pass: retain the core C1-C3 result if supported and call the original
  candidates hypothesis-generating.

**Strongest computationally allowed wording**

After internal donor evidence, C2/C3, candidate phenotype, C7, and external
support have passed, wording may describe robust network-nominated systems
associated with a replicated respiratory endpoint.

Do not use “three regulators drive mitochondrial failure.” Causal and
functional wording requires direct experiments.

**Outputs**

```text
results/<version>/post_phase13_review/final_claim_to_evidence_matrix.tsv
results/<version>/post_phase13_review/final_allowed_wording.md
results/<version>/post_phase13_review/final_limitations.md
results/<version>/post_phase13_review/final_analysis_inventory.tsv
```

---

## I. Validation evidence hierarchy

Technical correctness and scientific support must be reported separately.

| Level | Evidence | What it can support | What remains forbidden |
|---:|---|---|---|
| 0 | Status, hashes, schemas, row counts, and blocking checks | The analysis bundle is complete and reproducible | Any biological claim by itself |
| 1 | Phase 13 direct donor modifier plus FDR, CI, effect-size, and stability gates | Internally supported C1 RNA-expression modifier in an exact context | Context specificity, C3, replication, function, causality |
| 2 | Phase 14 direct between-context test | The modifier differs between named broad contexts | Fine-subtype exclusivity or independent replication |
| 3 | Phase 15 compatible endpoint gate | General or modifier-specific mitonuclear RNA-expression relationship | Mitochondrial function or causal regulation |
| 4 | C4-C6 named readout, target-excluded program, non-circular bridge, and stability | Candidate phenotype compatible with the frozen endpoint | Robust network nomination or causality |
| 5 | C7 two null families, perturbation stability, and alternative donor network | Robust network-nominated association | Activation, inhibition, mediation, or causality |
| 6 | C8 independent RNA in different donors | Cross-donor replication of the frozen expression result | Protein/function evidence |
| 7 | C9 protein | Orthogonal protein support; independent if donors also differ | Causality or direct respiratory function |
| 8 | Context-relevant perturbation plus rescue and direct functional assay | Potential causal and functional support | Automatic generalization to human disease populations |

### I.1 Important labels

- Phase 14 and Phase 15 are **new same-cohort analyses**, not replication.
- A second network is **network robustness**, not independent biological
  replication.
- Protein from the same ROSMAP donors is **same-cohort orthogonal support**.
- Different donors plus RNA is **independent RNA replication**.
- Different donors plus protein is **independent orthogonal support**.

---

## J. Figure and deliverable plan

### J.1 Figure 1: Phase 13 C1 landscape and evidence

**Purpose**

Show the complete Phase 13 result rather than only selected significant rows.

**Panels**

1. **196-row signed landscape**
   - seven contexts in frozen order;
   - seven modifiers in frozen order;
   - four module panels;
   - symmetric zero-centered color scale;
   - distinct marks for supported, provisional, small, precise-null,
     inconclusive, and not-testable.
2. **Direct-respiratory forests**
   - all 98 rows for the 13-gene mtDNA and 86-gene nuclear OXPHOS modules;
   - point estimate and 95% CI;
   - zero line;
   - shaded `[-0.25,+0.25]` project threshold band;
   - minimum required-group donor count.
3. **Detailed row explanations**
   - one point per donor in the four required groups;
   - adjusted AD-minus-NCI component effects;
   - formal direct modifier estimate, CI, q, and donor counts.
4. **Stability atlas**
   - bootstrap and balanced-resample distributions;
   - leave-one-donor-out estimates;
   - PC1, 50-nucleus, QC, severe-QC, and omission results.
5. **Gene-support atlas**
   - every admitted module member, not only DEGs;
   - signed gene modifier estimate and CI;
   - frozen complex/category order.
6. **Testability and QC**
   - 20/50-nucleus donor counts;
   - module coverage;
   - reasons for not-testable rows.

### J.2 Figure 2: Phase 14 cell-context heterogeneity

Show:

- 28 omnibus effects/statuses;
- direct context-pair estimates and CIs;
- the matching Phase 13 context effects;
- paired-donor counts; and
- bootstrap/leave-one-donor-out stability.

Do not display “significant here, not significant there” as the test.

### J.3 Figure 3: Phase 15 mitonuclear relationship

Show:

- donor mtDNA-versus-nuclear score scatter;
- cross-fitted NCI reference;
- donor residuals;
- general and modifier endpoint forests;
- group-specific slopes over shared predictor ranges; and
- bootstrap, fold, PC1, normalization, gene/complex, and donor-influence
  checks.

### J.4 Figure 4: candidate phenotype evidence

Use one row per candidate, displaying:

- exact context and comparison;
- named readout effect and CI;
- target-excluded local-program effect and CI;
- companion respiratory result;
- non-circular association with the authorized shared endpoint;
- donor stability; and
- `convergence_eligible = yes/no/inconclusive`.

No causal arrows should be used.

### J.5 Figure 5: conditional C7 network evidence

Only candidates authorized for C7 appear. Show:

- layer-3 subnetwork for explanation;
- query-null percentile;
- topology-null percentile;
- edge-perturbation rank stability;
- alternative-network support; and
- distinctness after removing the shared respiratory core.

Network links should be labeled “association” or “network edge,” not
activation or inhibition.

### J.6 Figure 6: external RNA and protein evidence

Show standardized effects and CIs for:

- ROSMAP discovery;
- independent RNA replication;
- independent protein support;
- same-cohort protein support;
- measured but unsupported; and
- not measured.

### J.7 Required package for every figure

Each figure must include:

- plotted-data TSV or TSV.GZ;
- SVG or PDF vector output;
- 300-dpi PNG preview;
- caption;
- short methods note;
- analysis version and source-result IDs;
- figure checks/status; and
- a colorblind and grayscale readability check.

Use at least 7-point text at final size. Do not use a red-green scale, 3D
graphics, or significance stars in place of q values and gate status.
Not-testable values must be gray/blank, not plotted as zero.

### J.8 Suggested separate Phase 13 figure bundle

Do not write figure artifacts into the immutable 32-file Phase 13 production
bundle. A suitable separate root is:

```text
results/figures/phase13_respiratory_modifier/
```

A figure renderer may validate and reformat saved Phase 13 outputs, but it must
not refit models, recalculate module scores, replace q values, or change gates.
The exact proposed filenames are listed once, under the Outputs part of
[Task H.3](#h3-task-3-create-the-phase-13-evidence-figure-package), to avoid
maintaining two conflicting file lists.

---

## K. Verified reference layer or search strategy

### K.1 Local authoritative plans

- [Phase 13 respiratory modifier plan](phase_13_respiratory_modifier_plan.md)
- [Phase 14 modifier heterogeneity plan](../phase_14_modifier_hetrogeneity/phase_14_modifier_heterogeneity_plan.md)
- [Phase 15 mitonuclear coupling plan](../phase_15_mitonuclear_coupling/phase_15_mitonuclear_coupling_plan.md)
- [Deep-dive next-steps plan](../deep_dive_research/deep_dive_next_steps_plan.md)
- [Beginner guide to the claims and candidates](../deep_dive_research/beginner_guide_to_core_claims_and_three_candidate_systems.md)
- [Four respiratory programs](../deep_dive_research/four_respiratory_module_program.md)
- [Additional candidate and secondary modules](../deep_dive_research/more_module_programs.md)
- [OXPHOS complexes and genes tutorial](../deep_dive_research/oxphos_pathway_complexes_and_genes_tutorial.md)
- [Related-paper directory](../related_papers/)

### K.2 Formal literature status

No new formal external references were verified for this roadmap. Do not add a
PMID, DOI, title, author list, or dataset accession without direct verification.

If a formal literature layer is later requested, search and verify these
categories separately:

1. AD single-nucleus studies of mitochondrial/OXPHOS expression;
2. sex/APOE interaction analysis in AD brain transcriptomics;
3. donor-aware pseudobulk and direct interaction methods;
4. mitonuclear expression imbalance/coupling methods;
5. independent AD single-nucleus RNA resources with sex/APOE metadata;
6. AD brain proteomics for OXPHOS and candidate proteins; and
7. perturbation evidence for the three candidate systems.

Only directly verified primary papers or official resource documentation
should be cited.

---

## L. Self-critical risk review

### L.1 Strongest part of the design

The strongest component is the prespecified donor-level
difference-of-differences design with explicit effect sizes, CIs, FDR families,
sample-size rules, bootstrap, and leave-one-donor-out checks.

### L.2 Most assumption-dependent part

The most assumption-dependent components are:

- the biological completeness of the frozen gene modules;
- broad cell-context mappings;
- the NCI reference used for C3 residuals;
- linear coupling-slope interpretation;
- the final C6 target-excluded program; and
- comparability of any external brain region, diagnosis, and taxonomy.

### L.3 Most likely sources of false positives

- many tested contexts, contrasts, modules, endpoints, and candidate rows;
- small e2 subgroups, especially male e2;
- post-result choice of pathway, fine type, or network layer;
- same donors reused across multiple analyses;
- mtDNA transcript abundance and mitochondrial-read composition;
- network hubs that are easy to nominate; and
- query genes that nominate themselves or close neighbors.

### L.4 Results most likely to be overinterpreted

| Observed result | Tempting but unsupported interpretation | Correct interpretation |
|---|---|---|
| Significant in astrocytes but not neurons | Astrocyte-specific | Observed in astrocytes; specificity needs Phase 14 direct comparison |
| mtDNA score differs from nuclear score | Mitochondria are decoupled or failing | Relative RNA-expression imbalance; slope evidence is required for coupling language |
| C3 residual changes | ATP production decreased | Donors depart from the NCI RNA-expression relationship |
| Candidate is top KDA hit | Candidate regulates the pathway | Network-nominated association requiring null controls and experiments |
| RNA and protein agree | Candidate is causal | Cross-modality association, not causality |
| Large e2 estimate | Confirmed strong biology | Potentially important but low-power unless donor/stability/external rules pass |

### L.5 Likely reviewer criticisms

- donor imbalance across sex/APOE groups;
- low-powered e2 comparisons;
- broad classes hiding opposing fine-subtype effects;
- postmortem RNA quality and mitochondrial-read artifacts;
- same-cohort reuse across Phases 11-15;
- absence of direct mitochondrial functional measures;
- network circularity and hub bias;
- external region/platform/taxonomy differences; and
- overclaiming specificity, regulation, or mechanism.

### L.6 Fallback plan if the key signal collapses

1. Do not replace it with a newly searched module.
2. Report the exact supported, null, inconclusive, or not-testable result.
3. If C1 fails, remove the sex/APOE respiratory-abundance clause.
4. Still run Phase 15 because C3 is a separate question.
5. If C2 fails, use “observed in the analyzed context,” not “specific.”
6. If C3 fails but nuclear OXPHOS C1 passes, describe a nuclear respiratory
   expression modifier, not a mitonuclear change.
7. Remove each candidate that fails its own phenotype or network gate.
8. Stop convergence wording if fewer than two candidate systems survive.
9. Keep secondary modules exploratory and clearly labeled.
10. Treat a careful negative result as a valid outcome rather than reopening
    the discovery search.

---

## Appendix A. Compact claim dependency map

| Claim | Question | Required evidence | Can another claim rescue it? |
|---|---|---|---|
| C1 | Does sex/APOE modify the AD respiratory-program effect? | Phase 13 direct donor modifier gate | No |
| C2 | Does that modifier differ between broad contexts? | Phase 14 direct omnibus/pair gate plus matching supported C1 row | No |
| C3 | Does the mtDNA-nuclear RNA relationship change? | Phase 15 two-of-three compatible endpoint gate | No; C3 can pass when C1 fails |
| C4 | Does `APOE–TUFM` have the predicted astrocyte phenotype? | Named readout, target-excluded translation, exact context/comparison, stability | C5/C6 cannot rescue it |
| C5 | Does `LAMTOR5–ATP5IF1` have the predicted neuronal phenotype? | Named readout, target-excluded Complex V, exact context/comparison, stability | C4/C6 cannot rescue it |
| C6 | Does `GABARAPL2–CHCHD2/PARK7` have the predicted excitatory phenotype? | Primary `CHCHD2`, frozen target-excluded program, exact context/comparison, stability | `PARK7` cannot rescue `CHCHD2`; C4/C5 cannot rescue it |
| C7a-c | Does each candidate beat fair network controls? | Candidate-specific two-null, perturbation, and alternative-network gate | One candidate cannot rescue another |
| C8 | Does the frozen RNA result replicate in different donors? | Frozen external RNA test | Same-cohort analysis cannot rescue it |
| C9 | Is there protein support? | Frozen protein result with coverage | Missing protein is not failure or support |

## Appendix B. Immediate post-Phase 13 checklist

### Trust the run

- [ ] Require `validation_status = validated_complete`.
- [ ] Confirm all declared Phase 13 files and hashes.
- [ ] Confirm all blocking checks and stages passed.
- [ ] Confirm 7 contexts, 7 modifiers, 4 modules, and 196 rows.
- [ ] Confirm every row has a terminal status.

### Lock C1

- [ ] Reproduce the 196-row join across manifests, results, `camera`, stability,
  and gates.
- [ ] Reproduce BH correction without refitting the model.
- [ ] Audit every supported/provisional/precise-null rule.
- [ ] Recompute the overall C1 label from gate rows as a QA check.
- [ ] Freeze exact allowed wording and next-branch permissions.

### Communicate C1

- [ ] Build the 196-row landscape.
- [ ] Build the 98-row direct-respiratory forest.
- [ ] Build row-explanation pages for all supported/provisional/small rows.
- [ ] Build stability, gene-support, and testability/QC atlases.
- [ ] Save plotted data, vector output, PNG, captions, methods, and checks.

### Run the Standard core

- [ ] Approve Phase 14 Minerva production after Phase 13 validates.
- [ ] Revalidate the completed Phase 15 local pilot and approve Phase 15
  Minerva production only after Phase 13 validates.
- [ ] Freeze the C4-C6 target-excluded modules and multiplicity families.
- [ ] Resolve the C6 quality-control-versus-mitophagy definition.
- [ ] Run C1-C6 and hold the locked review.
- [ ] Write `round2_authorization_manifest.tsv`.
- [ ] Audit and freeze one feasible external or orthogonal validation layer;
  if none is suitable, label the result an internally complete Standard core.

### Later work only for survivors

- [ ] Run C7 only for authorized candidate rows.
- [ ] Audit external RNA/protein feasibility before effects.
- [ ] Freeze validation targets and mappings.
- [ ] Run C8/C9 without rediscovery.
- [ ] Consider perturbation/rescue only for the strongest survivors.
