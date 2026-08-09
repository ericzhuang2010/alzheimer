# Phase 14: Donor-Level Test of Respiratory Modifier Heterogeneity Across Broad Cell Contexts

## Status and phase boundary

This document defines the scientific, implementation, execution, output, and
completion plan for Phase 14.

Plan status: **local pilot approved and executed on 2026-08-08;
Minerva production remains unapproved**.

Phase 14 tests **Claim 2 (C2), Modifier heterogeneity**:

> Does the sex/APOE modification of an AD-associated mitochondrial respiratory
> expression program differ between broad brain cell contexts?

Phase 14 production depends on a complete, independently validated Phase 13
production bundle. It must not run on partial, pilot, or manually copied Phase
13 outputs. The local pilot is the explicit exception described below: it uses
only a deterministic synthetic Phase 13-compatible fixture and cannot produce
scientific evidence.
The context comparisons, score-comparability rules, effect-size threshold,
multiple-testing families, and gate rules must be approved before anyone opens
the new Phase 14 results.

Executing the local pilot does not change Phase 13 results or authorize Phase
14 production.

### Short names

- Claim 1: **Respiratory modifier**
- Claim 2: **Modifier heterogeneity**
- Claim 3: **Mitonuclear coupling**

### Output roots

```text
results/local_pilot/14_modifier_heterogeneity/
results/minerva_production/14_modifier_heterogeneity/
```

Pilot files are nonfinal and must never be copied into, combined with, or
promoted in place to the production directory.

## What Phase 14 will and will not do

### Phase 14 will

1. use all seven broad Phase 13 cell contexts;
2. preserve donors as the independent biological samples;
3. recognize that the same donor may contribute several cell contexts;
4. rebuild comparable module/program scores using the same genes across all
   seven contexts;
5. estimate the seven frozen Phase 13 sex/APOE modifiers jointly by context;
6. run 28 omnibus tests of global context heterogeneity;
7. run all 588 direct pairwise context contrasts for localization;
8. apply prespecified FDR, effect-size, donor-overlap, stability, and Phase 13
   carry-forward gates; and
9. publish every supported, provisional, null, inconclusive, and untestable
   row with provenance.

### Phase 14 will not

- compare separate Phase 13 P values and call them different;
- treat a modifier that is significant in one context but not another as proof
  of context heterogeneity;
- use individual nuclei as independent observations;
- screen all 54 fine cell types;
- change the Phase 13 donor cohort, seven modifiers, or four modules/programs;
- select context pairs after viewing results;
- use Phase 08 DEGs, Phase 10 similarity scores, Phase 11 pathways, or Phase 12
  KDA results;
- test mitonuclear coupling, which belongs to Claim 3;
- test the three candidate systems;
- interpret RNA-expression heterogeneity as mitochondrial functional failure;
- claim that one context causes the result in another; or
- use “cell-type-specific” for a fine subtype.

Phase 14 concerns broad-cell-context heterogeneity. Fine-type localization is a
later, separately frozen analysis.

## The scientific question in plain language

Suppose the female-versus-male difference in the AD effect is `-0.8` score
units in astrocytes and `-0.1` in excitatory neurons. Phase 14 asks whether the
difference between those two modifier effects is itself supported:

```text
astrocyte modifier minus excitatory-neuron modifier
    = -0.8 - (-0.1)
    = -0.7
```

It is not enough to say:

```text
astrocytes: significant
excitatory neurons: not significant
```

Different P values can arise from different donor counts or uncertainty even
when the effects are similar. Claim 2 requires a direct between-context
contrast.

## Relationship to Phase 13

Phase 13 asks whether sex or APOE modifies an AD-associated module/program
effect within a broad cell context. Phase 14 asks whether that already defined
modifier differs between broad contexts.

```text
Phase 13 within-context modifier
    = [AD - NCI in group A]
      - [AD - NCI in group B]

Phase 14 between-context heterogeneity
    = Phase 13 modifier in context 1
      - Phase 13 modifier in context 2
```

Phase 14 therefore estimates a difference between two difference-of-differences.
It does not redefine the Phase 13 modifiers.

The Phase 13 plan is:

[Phase 13 respiratory modifier plan](../phase_13_repiratory_modifier/phase_13_respiratory_modifier_plan.md)

## Frozen scientific design

### Unit of analysis

The independent biological sample remains one donor. The analysis table is
long-form:

```text
one donor x one broad cell context x one module/program score
```

Several rows can belong to the same donor. Phase 14 must model that dependence
with a donor random intercept and must keep all of a donor's contexts together
during bootstrap and leave-one-donor-out analyses.

### Seven broad cell contexts

| Order | `context_id` | Plain name |
|---:|---|---|
| 1 | `astrocytes` | Astrocytes |
| 2 | `excitatory_neurons` | Excitatory neurons |
| 3 | `inhibitory_neurons` | Inhibitory neurons |
| 4 | `immune_cells` | Immune cells |
| 5 | `opcs` | Oligodendrocyte precursor cells |
| 6 | `oligodendrocytes` | Oligodendrocytes |
| 7 | `vasculature` | Vasculature cells |

These IDs, order, and donor/context eligibility must be inherited exactly from
the validated Phase 13 context and sample manifests.

### Four frozen modules/programs

In this plan, **module** and **program** mean the same prespecified gene set.
“Module” is used in code and filenames; “program” is used in biological
explanations.

| Order | `module_id` | Role in Claim 2 |
|---:|---|---|
| 1 | `mtdna_oxphos_13` | Direct respiratory module/program |
| 2 | `nuclear_oxphos_structural_86` | Direct respiratory module/program |
| 3 | `mitochondrial_translation_155` | Respiration-supporting module/program |
| 4 | `mib_micos_inner_membrane_19` | Respiration-supporting module/program |

Only the first two modules can support the headline wording “respiratory
modifier heterogeneity.” Translation-only or membrane-only heterogeneity must
be named narrowly.

### Seven inherited direct modifiers

For sex `s`, APOE group `a`, context `c`, and module/program `m`, define:

```text
Delta(s,a,c,m) =
    adjusted mean score in AD
    - adjusted mean score in NCI
```

The seven Phase 13 modifiers are:

| Order | `contrast_id` | Modifier effect within context `c` |
|---:|---|---|
| 1 | `sex_F_minus_M__e2` | `Delta(Female,e2,c,m) - Delta(Male,e2,c,m)` |
| 2 | `sex_F_minus_M__e33` | `Delta(Female,e33,c,m) - Delta(Male,e33,c,m)` |
| 3 | `sex_F_minus_M__e4` | `Delta(Female,e4,c,m) - Delta(Male,e4,c,m)` |
| 4 | `apoe_e2_minus_e33__Female` | `Delta(Female,e2,c,m) - Delta(Female,e33,c,m)` |
| 5 | `apoe_e2_minus_e33__Male` | `Delta(Male,e2,c,m) - Delta(Male,e33,c,m)` |
| 6 | `apoe_e4_minus_e33__Female` | `Delta(Female,e4,c,m) - Delta(Female,e33,c,m)` |
| 7 | `apoe_e4_minus_e33__Male` | `Delta(Male,e4,c,m) - Delta(Male,e33,c,m)` |

Call the estimated value of one modifier `M(k,c,m)`, where `k` identifies the
frozen contrast.

### Twenty-one frozen context pairs

Seven contexts produce `choose(7,2) = 21` unordered pairs. The order below is
frozen before testing:

| Pair order | `context_1` | `context_2` |
|---:|---|---|
| 1 | `astrocytes` | `excitatory_neurons` |
| 2 | `astrocytes` | `inhibitory_neurons` |
| 3 | `astrocytes` | `immune_cells` |
| 4 | `astrocytes` | `opcs` |
| 5 | `astrocytes` | `oligodendrocytes` |
| 6 | `astrocytes` | `vasculature` |
| 7 | `excitatory_neurons` | `inhibitory_neurons` |
| 8 | `excitatory_neurons` | `immune_cells` |
| 9 | `excitatory_neurons` | `opcs` |
| 10 | `excitatory_neurons` | `oligodendrocytes` |
| 11 | `excitatory_neurons` | `vasculature` |
| 12 | `inhibitory_neurons` | `immune_cells` |
| 13 | `inhibitory_neurons` | `opcs` |
| 14 | `inhibitory_neurons` | `oligodendrocytes` |
| 15 | `inhibitory_neurons` | `vasculature` |
| 16 | `immune_cells` | `opcs` |
| 17 | `immune_cells` | `oligodendrocytes` |
| 18 | `immune_cells` | `vasculature` |
| 19 | `opcs` | `oligodendrocytes` |
| 20 | `opcs` | `vasculature` |
| 21 | `oligodendrocytes` | `vasculature` |

The signed pairwise heterogeneity estimate is:

```text
H(k,c1,c2,m) = M(k,c1,m) - M(k,c2,m)
```

Positive `H` means the Phase 13 modifier is more positive, or less negative,
in `context_1`. Negative `H` means it is more negative, or less positive, in
`context_1`.

### Planned result grids

Phase 14 has four important grids:

```text
context-specific modifier estimates:
    7 contexts x 7 modifiers x 4 modules/programs = 196

global heterogeneity tests:
    7 modifiers x 4 modules/programs = 28

direct pairwise heterogeneity tests:
    21 context pairs x 7 modifiers x 4 modules/programs = 588

descriptive within-stratum AD effects:
    7 contexts x 6 sex/APOE strata x 4 modules/programs = 168
```

The 28 omnibus hypotheses and 588 pairwise localization hypotheses are separate
prespecified families. The 196 context modifier estimates and 168 stratum
effects explain those tests but are not additional Claim 2 hypotheses.

## Score comparability across contexts

### Why Phase 13 scores cannot be compared blindly

Phase 13 admits module genes separately in each context. If one context uses 80
nuclear OXPHOS genes and another uses 72, their scores represent slightly
different measured gene sets. A strict between-context test should compare the
same program definition.

### Primary common-gene rule

For each module/program, Phase 14 creates one common gene set before examining
heterogeneity results:

```text
common genes for module m =
    frozen Phase 13 module genes
    that map uniquely,
    pass the Phase 13 expression filter,
    and have finite nonzero NCI variance
    in all seven broad contexts
```

The common set must satisfy:

```text
common genes / frozen module genes >= 0.70
AND common genes >= 5
```

The mtDNA module additionally requires at least 10 of 13 genes.

If a module fails the all-context common-gene rule, its seven-context omnibus
and all of its pairwise primary rows are `not_testable_common_coverage`. A
pair-specific gene intersection may be reported as an exploratory sensitivity,
but it cannot rescue the frozen Claim 2 gate.

### Recalculate comparable scores

For each common gene `g` and context `c`, use eligible NCI donors in that
context to calculate:

```text
mu(g,c) = mean NCI TMM logCPM
sd(g,c) = SD of NCI TMM logCPM

z(d,g,c) = [logCPM(d,g,c) - mu(g,c)] / sd(g,c)
```

For module/program `m`:

```text
raw_common_mean_z(d,m,c) =
    mean z(d,g,c) over the common genes in m
```

Then standardize the donor module score within the NCI distribution of the
same context:

```text
common_score(d,m,c) =
    [raw_common_mean_z(d,m,c) - mean_NCI(raw_common_mean_z)]
    / sd_NCI(raw_common_mean_z)
```

One score unit is one NCI donor-level module/program standard deviation in that
context. The genes are common across contexts; the NCI centering and scaling
parameters remain context-specific.

Significant-DEG status, P values, q values, and Phase 13 effect sizes are not
used to select or weight common-score genes.

### Required score sensitivities

- Phase 13 original context-specific admitted-gene score;
- common-gene NCI-trained PC1 score, deterministically oriented toward the
  primary mean-z score;
- pair-complete donor score analysis;
- profiles meeting the 50-nucleus threshold; and
- severe-QC exclusion and mitochondrial-read-fraction adjustment.

The common-gene mean-z score is primary. Sensitivities cannot replace a failed
primary result.

## Donor and contrast eligibility

### Context-level eligibility

For one modifier in one context:

- every one of its four required diagnosis-by-group cells needs at least five
  unique eligible donors for estimation;
- 5-9 donors in any required cell makes the context modifier provisional;
- at least 10 donors in every required cell is required for an internally
  confirmatory named-context result; and
- the design must be full rank and the common module/program must pass coverage.

### Pair-level eligibility

For a direct comparison between contexts `c1` and `c2`, count donors represented
in both contexts within each of the four required diagnosis-by-group cells:

- fewer than five paired donors in any required cell gives
  `not_testable_low_paired_donor_count`;
- 5-9 paired donors permits a provisional estimate; and
- at least 10 paired donors in every required cell is required for an
  internally confirmatory pairwise claim.

The primary mixed model can use incomplete context profiles, but every named
pair must also retain its direction in a pair-complete analysis containing only
donors observed in both contexts.

### Omnibus eligibility

One seven-context omnibus row is testable only when:

- the common module/program passes all-context coverage;
- the modifier is estimable in all seven contexts;
- the repeated-donor model converges with a positive finite donor variance and
  finite context residual variances; and
- the donor-overlap graph connecting the seven contexts is connected for the
  required groups.

Failure of the seven-context omnibus does not automatically make every pair
untestable. Eligible pairwise estimates remain visible but cannot earn the
strict global-heterogeneity sentence without a passing parent omnibus test.

## Primary repeated-donor model

Stack the common scores for one module/program into one long table. Fit one
model per module with `nlme::lme`:

```text
fixed:
    common_score
        ~ 0
          + context:diagnosis_sex_APOE_group
          + age_death_scaled
          + pmi_scaled
          + study

random:
    ~ 1 | projid

context-specific residual variance:
    varIdent(~ 1 | context)

method:
    REML
```

The context-by-group coefficients allow every one of the 12 diagnosis, sex,
and APOE group means to differ across contexts. The random donor intercept
accounts for repeated profiles from the same person. `varIdent` prevents the
model from assuming equal residual variation in all seven contexts.

Use exact model covariance to derive every context modifier, omnibus test,
pairwise estimate, standard error, confidence interval, and P value. Do not fit
588 separate models and do not calculate the pairwise standard error by adding
two Phase 13 standard errors as if they were independent.

Required model sensitivities are:

- homogeneous residual variance;
- context-specific age and PMI slopes when the expanded model remains full
  rank;
- pair-complete donors;
- common-gene PC1 scores; and
- the frozen QC and nucleus-threshold profiles.

## Omnibus and pairwise tests

### Twenty-eight omnibus tests

For modifier `k` and module/program `m`, the omnibus null is:

```text
M(k,astrocytes,m)
= M(k,excitatory_neurons,m)
= M(k,inhibitory_neurons,m)
= M(k,immune_cells,m)
= M(k,opcs,m)
= M(k,oligodendrocytes,m)
= M(k,vasculature,m)
```

Test this as a six-degree-of-freedom Wald test using a frozen full-rank contrast
basis. Astrocytes may be the algebraic reference, but the omnibus P value must
be invariant to the chosen full-rank basis.

### Five hundred eighty-eight pairwise tests

For every one of the 21 context pairs, derive the same modifier difference:

```text
H(k,c1,c2,m) = M(k,c1,m) - M(k,c2,m)
```

Report the estimate, exact model-based SE, 95% CI, P value, q value, the four
paired donor counts, full donor counts, direction, and parent omnibus status.

### Multiple-testing correction

Freeze two primary BH families:

```text
Family H14-omnibus:
    7 modifiers x 4 modules/programs = 28 P values

Family H14-pairwise:
    21 pairs x 7 modifiers x 4 modules/programs = 588 P values
```

Apply BH separately to testable rows in the two families. Preserve all 28 and
588 structural rows; untestable rows retain `p = NA` and `q = NA` with an exact
reason.

Pairwise tests are not corrected only within an attractive omnibus row. All 588
planned pairwise P values belong to the frozen pairwise family.

## Effect-size and uncertainty rules

The proposed Phase 14 smallest effect size of interest is inherited from the
Phase 13 standardized-score scale:

```text
absolute between-context modifier difference >= 0.25
NCI module/program-score standard deviations
```

This number must be approved before results are opened. It is a project rule,
not a universal biological constant.

A named pair meets the primary effect rule when:

```text
absolute H >= 0.25
AND the model-based 95% CI excludes 0
```

A precise equivalence-to-zero result requires the entire 95% CI to lie inside:

```text
[-0.25, +0.25]
```

A q value above 0.05 is not automatically a precise null.

## Stability analyses

Every testable omnibus and pairwise row receives the same prespecified checks.

### Donor bootstrap

Run 1,000 repetitions. In each repetition:

1. resample whole donors with replacement within each of the 12 diagnosis,
   sex, and APOE groups;
2. keep every sampled donor's available contexts together;
3. rebuild context-specific TMM normalization from the Phase 13 broad counts;
4. keep the full-data common gene membership fixed while rebuilding NCI means,
   SDs, and module/program scores;
5. refit the four repeated-donor models; and
6. derive all testable omnibus and pairwise estimates.

Save replicate estimates, failure reasons, bootstrap medians, percentile 95%
intervals, sign-retention fractions, and successful-repetition fractions.

### Leave one donor out

Remove one donor and all of that donor's contexts, rebuild scores, refit the
models, and derive every eligible estimate. A supported pair must have no sign
reversal:

```text
primary H x leave-one-donor-out H < 0
```

### Pair-complete analysis

For each pair, refit using only donors represented in both contexts. The direct
pair estimate must retain its primary direction and remain scientifically
compatible with the primary interval.

### Fifty-nucleus analysis

Repeat with donor/context profiles meeting the frozen Phase 13 50-nucleus
threshold. A result that becomes untestable is labeled as such; it is not called
a contradictory null.

### Balanced group resampling

For each modifier, downsample its four required diagnosis-by-group cells to the
smallest eligible donor count while retaining each selected donor's contexts.
Run 1,000 repetitions and derive the same estimates.

### Score and QC sensitivities

- common-gene NCI-trained PC1;
- original Phase 13 context-specific admitted-gene score;
- mitochondrial-read-fraction adjustment;
- frozen severe-QC exclusion;
- homogeneous versus context-specific residual variance; and
- omission of one mtDNA gene, OXPHOS complex, translation category, or
  membrane subcomponent at a time where relevant.

Mandatory stability criteria for a supported pair are:

- at least 950 of 1,000 bootstrap repetitions succeed;
- at least 80% of successful bootstrap estimates retain the primary sign;
- no leave-one-donor-out sign reversal;
- pair-complete analysis retains the direction;
- common-gene PC1 retains a compatible direction; and
- required QC and model sensitivities do not reverse the conclusion.

## Claim 2 gates

### Gate for one named context pair

A pairwise row is `supported` only when all of the following hold:

1. its parent 28-row omnibus test has `q <= 0.05`;
2. the direct pairwise test has family-wide `q <= 0.05`;
3. `absolute H >= 0.25` and the 95% CI excludes zero;
4. at least one of the two matching Phase 13 context rows is `supported` for
   the same modifier and module/program;
5. the Phase 14 common-score context effects are directionally compatible with
   the carried Phase 13 result;
6. every required paired group has at least 10 donors;
7. bootstrap, leave-one-donor-out, pair-complete, PC1, QC, and model
   sensitivities pass; and
8. the module/program is interpreted according to its direct-respiratory or
   supporting role.

Five to nine paired donors can produce `provisional_low_power` only when all
other support rules pass. It cannot produce an internally confirmatory Claim 2
statement.

### Frozen pairwise row statuses

Assign statuses in this order:

1. `not_testable` when coverage, donor count, rank, convergence, covariance, or
   a required input prevents estimation;
2. `provisional_low_power` when all non-count support rules pass but a required
   paired group has 5-9 donors;
3. `supported` when every gate rule passes;
4. `statistically_detectable_but_small` when q and nonzero-CI rules pass but
   `absolute H < 0.25`;
5. `not_supported_precise_null` when the full CI is inside
   `[-0.25,+0.25]`; and
6. `inconclusive` otherwise.

Store every component as a separate Boolean or status field so the summary
label never hides why a row passed or failed.

### Global omnibus statuses

For each of the 28 modifier-by-module/program rows, assign:

| Status | Meaning |
|---|---|
| `supported_and_localized` | Omnibus q passes and at least one pair is supported |
| `global_only` | Omnibus q passes but no named pair passes the complete pair gate |
| `provisional` | Heterogeneity is present but only low-power pairs carry it |
| `not_supported_precise_null` | All estimable pair intervals are within the SESOI range and omnibus does not pass |
| `inconclusive` | Available evidence cannot distinguish meaningful heterogeneity from no heterogeneity |
| `not_testable` | The omnibus model or common-score outcome cannot be estimated |

### Overall scientific decision

The Phase 14 production bundle stores one of:

```text
supported_both
supported_sex_only
supported_apoe_only
supporting_program_only
provisional
not_supported
inconclusive
not_testable
```

Only supported rows in `mtdna_oxphos_13` or
`nuclear_oxphos_structural_86` can produce the first three headline decisions.

### Allowed wording

If a direct-respiratory pair passes, an allowed sentence is:

> In ROSMAP donor-level profiles, the [exact sex/APOE] modification of the
> AD-associated [exact respiratory program] expression effect differed between
> [context 1] and [context 2].

If only the global omnibus passes, say:

> The modifier showed evidence of heterogeneity across the seven analyzed broad
> cell contexts, but no individual context pair passed the complete localization
> gate.

Do not say “specific to context 1” unless the direct comparison with the named
alternative context passed. Do not generalize broad-context evidence to every
fine subtype.

## Inputs and dependencies

### Required Phase 13 production state

Require:

```text
results/minerva_production/13_respiratory_modifier/
```

with `respiratory_status.tsv` reporting:

```text
validation_status = validated_complete
contexts = 7
modules = 4
modifier_contrasts = 7
planned_primary_tests = 196
```

Every declared Phase 13 artifact hash and every blocking Phase 13 check must
validate independently.

### Required Phase 13 files

| File | Phase 14 use |
|---|---|
| `respiratory_analysis_manifest.tsv` | Frozen Phase 13 definitions and provenance |
| `respiratory_cell_context_manifest.tsv` | Seven context IDs and order |
| `respiratory_contrast_manifest.tsv` | Seven modifier definitions and coefficient vectors |
| `respiratory_module_manifest.tsv` | Four module/program definitions and roles |
| `respiratory_module_members.tsv` | Frozen 273 membership rows and assay mappings |
| `respiratory_donor_samples.tsv.gz` | Donor/context groups, eligibility, nuclei, and QC |
| `respiratory_pseudobulk_counts.rds` | Seven all-gene broad count matrices for score rebuilding and bootstrap |
| `respiratory_expression_bundle.rds` | Frozen tested genes, TMM/logCPM, and designs |
| `respiratory_module_coverage.tsv` | Context-specific admission needed for the common-gene intersection |
| `respiratory_nci_reference_parameters.tsv.gz` | Phase 13 reference checks |
| `respiratory_donor_module_scores.tsv.gz` | Original Phase 13 scores for sensitivity and carry-forward checks |
| `respiratory_pc1_loadings.tsv.gz` | Phase 13 score sensitivity provenance |
| `respiratory_module_results.tsv` | Exact context modifier estimates and C1 evidence |
| `respiratory_stability_summary.tsv` | Phase 13 carry-forward stability fields |
| `respiratory_gate_decisions.tsv` | Required C1 status for the Claim 2 gate |
| `respiratory_checks.tsv` | Upstream blocking checks |
| `respiratory_artifacts.tsv` | Input hash validation |
| `respiratory_status.tsv` | Terminal technical and scientific state |

### Explicit non-inputs

The Phase 14 scientific script must not read:

- Phase 08 DEG results;
- Phase 10 similarity scores;
- Phase 11 pathway results;
- Phase 12 KDA results;
- fine-cell normalized matrices;
- candidate-system tables; or
- figures or manually edited summaries.

## Construction and analysis workflow

### Task 1: freeze Phase 14 definitions

**Inputs:** this approved plan and the validated Phase 13 manifests.

**Steps:**

1. write the seven contexts in frozen order;
2. write the 21 context pairs;
3. inherit the seven modifier coefficient vectors;
4. inherit the four modules/programs and roles;
5. freeze the 28-row omnibus and 588-row pairwise families;
6. approve SESOI, donor, stability, and gate rules;
7. freeze random seeds, software versions, schemas, and paths; and
8. set `definitions_frozen = TRUE`.

### Task 2: validate Phase 13

1. require `validated_complete` production status;
2. verify every required Phase 13 input resolves to a declared upstream
   artifact and validate its stored hash;
3. verify file hashes, schemas, row counts, and unique keys;
4. require exactly 7 contexts, 7 modifiers, 4 modules, and 196 Phase 13 rows;
5. verify donor IDs and metadata agree across counts, samples, scores, and
   results; and
6. stop on any blocking failure.

### Task 3: build common comparable scores

1. intersect admitted module genes across all seven contexts;
2. apply common coverage rules before viewing heterogeneity estimates;
3. rebuild NCI gene means and SDs by context;
4. calculate common mean-z scores and NCI-SD standardized scores;
5. build and orient common-gene NCI-trained PC1 scores;
6. audit Phase 13 original versus Phase 14 common scores; and
7. save every included and excluded gene with a reason.

### Task 4: build overlap and test manifests

1. create donor-by-context availability and group-count tables;
2. count pair-complete donors in each required group;
3. verify the donor-overlap graph;
4. write all 28 omnibus rows;
5. write all 588 pairwise rows;
6. assign eligibility without viewing estimates; and
7. retain every untestable row with a reason.

### Task 5: fit four joint mixed models

1. stack long common scores;
2. fit one `nlme::lme` model per module/program;
3. record convergence, rank, variance components, residual diagnostics, and
   donor influence;
4. derive 196 context modifier estimates;
5. derive 168 descriptive stratum effects;
6. derive 28 omnibus tests; and
7. derive all 588 direct pairwise tests using exact model covariance.

### Task 6: apply multiplicity and effect rules

1. apply BH to the 28 omnibus P values;
2. apply BH separately to the 588 pairwise P values;
3. calculate effect-size and equivalence fields;
4. join parent omnibus status to every pair; and
5. preserve untestable rows with `p = NA` and `q = NA`.

### Task 7: run stability analyses

Run donor bootstrap, leave-one-donor-out, pair-complete, 50-nucleus,
group-balanced, PC1, original-score, QC, residual-variance, and omission
analyses. Save every replicate and failure reason, not only summaries.

### Task 8: apply gates and publish

1. calculate row statuses without manual scoring;
2. calculate 28 global statuses;
3. calculate the overall scientific decision;
4. create exact allowed wording for every supported row;
5. retain all negative, provisional, inconclusive, and untestable results;
6. write checks and artifact hashes;
7. validate the complete staging bundle independently; and
8. publish `heterogeneity_status.tsv` last.

## Output and file contract

Final production root:

```text
results/minerva_production/14_modifier_heterogeneity/
```

| File | Required content |
|---|---|
| `heterogeneity_analysis_manifest.tsv` | One frozen analysis definition, approvals, versions, thresholds, and hashes |
| `heterogeneity_cell_context_manifest.tsv` | Exactly 7 inherited context rows |
| `heterogeneity_context_pair_manifest.tsv` | Exactly 21 frozen unordered context pairs |
| `heterogeneity_contrast_manifest.tsv` | Exactly 7 inherited modifier definitions |
| `heterogeneity_module_manifest.tsv` | Exactly 4 inherited module/program definitions and roles |
| `heterogeneity_common_module_members.tsv` | All 273 memberships with seven-context admission and exclusion fields |
| `heterogeneity_input_inventory.tsv` | Required Phase 13 paths, schemas, statuses, and hashes |
| `heterogeneity_source_checks.tsv` | Input identity, key, count, and provenance checks |
| `heterogeneity_donor_context_overlap.tsv` | Donor availability, pair-complete counts, and overlap-graph fields |
| `heterogeneity_omnibus_test_manifest.tsv` | Exactly 28 structural omnibus rows and eligibility |
| `heterogeneity_pairwise_test_manifest.tsv` | Exactly 588 structural pairwise rows and eligibility |
| `heterogeneity_common_scores.tsv.gz` | Common mean-z, standardized, and PC1 scores by donor/context/module |
| `heterogeneity_nci_reference_parameters.tsv.gz` | Context/gene and context/module NCI scaling parameters |
| `heterogeneity_context_modifier_effects.tsv` | Exactly 196 joint-model context modifier estimates |
| `heterogeneity_context_stratum_effects.tsv` | Exactly 168 descriptive AD-minus-NCI effects |
| `heterogeneity_omnibus_results.tsv` | Exactly 28 global heterogeneity results |
| `heterogeneity_pairwise_results.tsv` | Exactly 588 direct context-pair results |
| `heterogeneity_model_diagnostics.tsv` | Four model specifications, ranks, variance components, convergence, and residual diagnostics |
| `heterogeneity_pc1_loadings.tsv.gz` | Common-gene NCI-trained PC1 loadings and orientation fields |
| `heterogeneity_score_reliability.tsv` | Coverage and agreement between common, PC1, and Phase 13 scores |
| `heterogeneity_complete_case_results.tsv` | Exactly 588 pair-complete sensitivity rows |
| `heterogeneity_stability_replicates.tsv.gz` | Long-form bootstrap, LOO, balance, threshold, QC, and omission results |
| `heterogeneity_omnibus_stability_summary.tsv` | Exactly 28 omnibus stability summaries |
| `heterogeneity_pairwise_stability_summary.tsv` | Exactly 588 pairwise stability summaries |
| `heterogeneity_gate_decisions.tsv` | Exactly 588 component-by-component pair decisions |
| `heterogeneity_global_decisions.tsv` | Exactly 28 omnibus/global decisions |
| `heterogeneity_claim_summary.tsv` | Sex, APOE, direct-respiratory, supporting-program, and overall conclusions |
| `heterogeneity_stage_status.tsv` | Checkpoint dependencies, fingerprints, shard counts, times, and terminal states |
| `heterogeneity_checks.tsv` | Blocking and nonblocking checks |
| `heterogeneity_artifacts.tsv` | Declared paths, schemas, rows, bytes, and hashes |
| `heterogeneity_status.tsv` | One phase-level technical and scientific status row |

Every TSV begins with `schema_version`. Every final file is declared in the
artifact manifest. The final directory is flat, contains exactly these 31
files, contains no scratch subdirectory, and is published atomically.

## Phase 14 end state

### Scientific and technical end state

Production is technically complete when:

```text
validation_status = validated_complete
contexts = 7
context_pairs = 21
modifier_contrasts = 7
modules = 4
omnibus_rows = 28
pairwise_rows = 588
context_modifier_rows = 196
context_stratum_rows = 168
```

Every row has a terminal scientific status. No positive result is required for
technical completion.

### Source-controlled files added

| File | Purpose |
|---|---|
| `config/phase14_modifier_heterogeneity.yml` | Frozen design, model, pair order, thresholds, FDR, stability, paths, schemas, and seeds |
| `scripts/14_run_modifier_heterogeneity.R` | Validation, common-score construction, mixed models, contrasts, stability, gates, and atomic publication |
| `tests/test_phase14_modifier_heterogeneity.R` | Synthetic, unit, integration, and output-only validation tests |
| `docs/phase_14_modifier_hetrogeneity/phase_14_modifier_heterogeneity_plan.md` | This approved Phase 14 contract |

### Existing files modified

| File | Required change |
|---|---|
| `scripts/run_pipeline.R` | Register and dispatch global task `modifier_heterogeneity` after `respiratory_modifier` |
| `config/local_pilot.yml` | Add the Phase 14 config path and enable the local pilot task |
| `config/minerva_shared.yml` | Add the Phase 14 config path and enable Minerva production |

`nlme` is already pinned in `renv.lock`; no lockfile change is planned. If an
additional package becomes necessary, that is a plan deviation and must be
approved before results are opened.

### Files deleted

None. Phase 14 does not delete or overwrite source files, raw data, Phase 13
artifacts, or an existing validated Phase 14 bundle. Replacement runs build in
new scratch space and publish only after independent validation.

### Pipeline registration

```text
task_mode: modifier_heterogeneity
scope: global
stable_task_id: global:modifier_heterogeneity
output_schema: mitochondrial_modifier_heterogeneity_v1
dependency: global:respiratory_modifier
```

Both environment YAML files add:

```yaml
project:
  phase14_modifier_heterogeneity_config: config/phase14_modifier_heterogeneity.yml

scope:
  allowed_task_modes:
    - modifier_heterogeneity
```

The global task rejects `--rds-id`.

## Local pilot

The Phase 13 local pilot has only one pseudo-context and cannot test
between-context heterogeneity. Therefore, the Phase 14 local pilot must use a
deterministic synthetic Phase 13-compatible fixture with three repeated-donor
contexts. It tests code, covariance, contrast signs, missing-context handling,
schemas, and gates only.

Expected local-pilot dimensions:

```text
contexts = 3
context_pairs = 3
modules = 4
modifiers = 7
omnibus rows = 28
pairwise rows = 3 x 7 x 4 = 84
context modifier rows = 3 x 7 x 4 = 84
context stratum rows = 3 x 6 x 4 = 72
validation_status = nonfinal_smoke_test
scientific_decision = not_applicable_pilot
```

The synthetic fixture must contain known positive heterogeneity, known null,
precise equivalence, missing context, low paired-donor count, common-coverage
failure, sign reversal, singular covariance, PC1 orientation, and BH examples.

Planned commands:

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer

Rscript tests/test_phase14_modifier_heterogeneity.R

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase modifier_heterogeneity \
  --dry-run

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase modifier_heterogeneity

Rscript tests/test_phase14_modifier_heterogeneity.R \
  --validate-output results/local_pilot/14_modifier_heterogeneity \
  --expected-contexts 3 --expected-pairs 3 \
  --expected-omnibus-rows 28 --expected-pairwise-rows 84 \
  --expected-context-modifier-rows 84 --expected-stratum-rows 72 \
  --expected-status nonfinal_smoke_test
```

Pilot results cannot be used as Claim 2 evidence.

### Local pilot execution record

The local pilot was executed on 2026-08-08 after the user explicitly requested
local execution. Synthetic/unit tests, the pipeline dry run, the full pilot,
and independent output-only validation all passed. The atomically published
bundle is:

```text
results/local_pilot/14_modifier_heterogeneity/
```

Validated dimensions and terminal labels were:

```text
contexts = 3
context_pairs = 3
modules = 4
modifiers = 7
omnibus rows = 28
pairwise rows = 84
context modifier rows = 84
context stratum rows = 72
declared files = 31
validation_status = nonfinal_smoke_test
scientific_decision = not_applicable_pilot
```

All four pilot mixed models converged. All 24 blocking pilot checks passed.
This execution record is technical validation only and is not Claim 2 evidence.

## Minerva production

### Preflight

1. require a validated Phase 13 production status;
2. independently verify all Phase 13 input hashes and blocking checks;
3. require exactly seven contexts and complete context/module/contrast
   manifests;
4. approve and freeze the Phase 14 configuration;
5. pass synthetic tests and the local pilot;
6. verify Git, configuration, and lockfile parity;
7. cap numeric-library threads at one; and
8. inspect the one-task dry-run graph and analysis fingerprint.

### Commands

```bash
cd /sc/arion/work/zhuane01/alzheimer

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

Rscript tests/test_phase14_modifier_heterogeneity.R

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase modifier_heterogeneity \
  --dry-run

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase modifier_heterogeneity

Rscript tests/test_phase14_modifier_heterogeneity.R \
  --validate-output results/minerva_production/14_modifier_heterogeneity \
  --expected-contexts 7 --expected-pairs 21 \
  --expected-omnibus-rows 28 --expected-pairwise-rows 588 \
  --expected-context-modifier-rows 196 --expected-stratum-rows 168 \
  --expected-status validated_complete
```

### Checkpointing and publication

The analysis fingerprint covers the Phase 13 artifact manifest and hashes,
Phase 14 code, scientific configuration, pipeline configuration, execution
configuration, and `renv.lock`.

Checkpoint long-running bootstrap and balanced-resampling work by module and
replicate shard. A rerun with the same fingerprint resumes completed shards.
An incompatible fingerprint starts a new scratch tree.

Publication order is:

```text
build in scratch
-> finish every declared stage
-> write all scientific files into staging
-> write checks and artifact manifest
-> write status last inside staging
-> independently validate staging
-> atomically rename staging to the final directory
```

## Required blocking checks

Independent output validation must confirm:

- exactly 7 contexts, 21 context pairs, 7 modifiers, and 4 modules/programs;
- exactly 273 inherited membership rows;
- exactly 28 omnibus and 588 pairwise structural/result rows;
- exactly 196 context modifier and 168 context stratum rows;
- Phase 13 status is `validated_complete` and every input hash validates;
- donor/context and donor/group keys are unique and consistent;
- common genes are identical across all seven contexts within a module;
- common coverage and mtDNA minimum rules reproduce;
- NCI reference parameters use only eligible NCI donors from the matching
  context;
- all four mixed models use the frozen formula and converge or record an exact
  failure;
- random-donor and context residual variance estimates are finite when rows are
  declared testable;
- all 196 context modifier estimates reproduce from model coefficients;
- the six-degree-of-freedom omnibus contrasts are full rank;
- all 588 pairwise estimates and exact covariance-based SEs reproduce;
- both 28-row and 588-row BH corrections reproduce;
- pair-complete donor counts reproduce for all required groups;
- whole donors, never rows or nuclei, are resampled or omitted;
- at least 950 required bootstrap and balance repetitions succeed for a
  supported row;
- no supported row has a leave-one-donor-out sign reversal;
- every gate Boolean and status reproduces from named source fields;
- direct-respiratory and supporting-program roles are not mixed;
- pilot provenance is absent from production;
- all 31 declared output files exist with no undeclared final file or
  subdirectory;
- every declared artifact hash validates; and
- `heterogeneity_status.tsv` is written only after all blocking checks pass.

## Completion criteria

Phase 14 is complete only when:

1. definitions, common-score rules, model, thresholds, FDR families, and gates
   are approved and frozen;
2. the Phase 13 production dependency validates independently;
3. implementation and synthetic tests pass;
4. the three-context local pilot validates as nonfinal;
5. Minerva production publishes atomically;
6. all 28 omnibus and 588 pairwise rows have terminal statuses;
7. every required stability summary reproduces;
8. exact permitted wording follows the gates;
9. every input and output has validated provenance; and
10. independent output-only validation passes.

Production completion is `validation_status = validated_complete` regardless
of whether modifier heterogeneity is supported, absent, inconclusive, or not
testable.

## Implementation checklist

### Freeze

- [ ] Approve all seven contexts and their order.
- [ ] Approve all 21 unordered context pairs.
- [ ] Inherit and verify the seven modifier vectors and four modules/programs.
- [ ] Approve the common-gene rule and coverage minimums.
- [ ] Approve the mixed model and covariance-derived contrasts.
- [ ] Approve the 0.25 SESOI, FDR families, paired-donor rules, stability rules,
  and claim gates.
- [ ] Freeze configuration, schemas, seeds, software, code revision, and hashes.

### Implement

- [ ] Add Phase 14 config, script, tests, and pipeline registration.
- [ ] Validate Phase 13 status, artifacts, schemas, and hashes.
- [ ] Implement common-score rebuilding and audit tables.
- [ ] Implement overlap eligibility and all structural manifests.
- [ ] Implement four repeated-donor mixed models.
- [ ] Implement 28 omnibus and 588 exact pairwise contrasts.
- [ ] Implement both BH families and all effect-size fields.
- [ ] Implement donor bootstrap, LOO, complete-case, balance, score, QC, and
  model sensitivities.
- [ ] Implement gates, claim wording, checkpointing, atomic publication, and
  output-only validation.

### Validate and execute

- [x] Pass deterministic synthetic tests locally.
- [x] Validate the three-context, 84-pair-row local pilot as nonfinal.
- [ ] Confirm Phase 13 Minerva production is complete and immutable.
- [ ] Run Minerva tests and the Phase 14 dry run.
- [ ] Execute or resume the four-model production analysis and stability shards.
- [ ] Independently validate 28 omnibus, 588 pairwise, 196 context-modifier, and
  168 stratum rows.
- [ ] Verify all 31 files, schemas, hashes, and blocking checks.
- [ ] Publish `heterogeneity_status.tsv` last.

### Locked result review

- [ ] Assign every omnibus and pairwise row a terminal scientific status.
- [ ] Separate sex, APOE, direct-respiratory, and supporting-program results.
- [ ] Label all e2 and low-paired-donor evidence as provisional when required.
- [ ] Report global-only heterogeneity without inventing a named pair.
- [ ] Use “broad-cell-context heterogeneity,” not fine-cell specificity.
- [ ] Write exact permitted conclusions and the next-step authorization.
