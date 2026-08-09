# Phase 13: Donor-Level Test of Sex/APOE Modification of AD-Associated Mitochondrial Respiratory Programs

## Status and phase boundary

This document defines the reviewable implementation and execution plan for
Phase 13.

Plan status: **draft for review; not approved for execution**.

Creating this plan does not run the analysis. It does not change results from
Phases 00–12. The module definitions, effect-size threshold, and gate rules
must be approved before anyone opens the new Phase 13 results.

Phase 13 tests **Claim 1 (C1)**:

> Within a brain cell context, does Alzheimer disease change a prespecified
> mitochondrial expression program differently in different sex or APOE
> groups?

In simpler language, Phase 13 asks whether the AD-versus-NCI difference is
different between two groups of people.

For example:

```text
female APOE e4 AD effect
    = average expression difference between female e4 AD and female e4 NCI

female APOE e33 AD effect
    = average expression difference between female e33 AD and female e33 NCI

C1 comparison
    = female e4 AD effect minus female e33 AD effect
```

The people, called donors, remain the independent samples. Nuclei from one
donor are added together; different donors are never merged into one sample.

Local-pilot and Minerva-production outputs are separate:

```text
results/local_pilot/13_respiratory_modifier/
results/minerva_production/13_respiratory_modifier/
```

Pilot files must never be copied into, combined with, or promoted in place to
the production directory.

### What Phase 13 will do

Phase 13 will:

1. build one all-gene expression profile per donor and broad cell class;
2. test the [seven direct sex/APOE differences](#seven-direct-modifier-contrasts)
   in the AD effect: female minus male within APOE e2, e33, and e4; e2 minus
   e33 within females and males; and e4 minus e33 within females and males;
3. test four mitochondrial gene programs chosen before the new results;
4. keep gene-level, donor-score, and gene-set evidence separate;
5. measure uncertainty and donor-to-donor variation;
6. stress-test every planned result; and
7. make an explicit C1 decision without hiding negative or untestable rows.

### What Phase 13 will not do

Phase 13 must **not**:

- use nuclei as if they were independent people;
- conclude that two groups differ merely because one has a small P value and
  the other does not;
- use the Zhang–Yu similarity score as the C1 test;
- use KDA or any Phase 12 key-driver result;
- test whether the result is statistically different between cell types,
  which belongs to Claim 2;
- test whether mtDNA and nuclear expression become uncoupled, which belongs to
  Claim 3;
- test APOE–TUFM, LAMTOR5–ATP5IF1, or
  GABARAPL2–CHCHD2/PARK7 candidate systems;
- select a module, contrast, threshold, or cell class after seeing Phase 13
  significance;
- interpret RNA abundance as direct proof of oxygen consumption, ATP
  production, or mitochondrial function;
- describe an association as causal; or
- draw or publish final figures.

Phase 13 will create validated, figure-ready data. A later figure workflow may
read the final Phase 13 bundle without changing the statistical analysis.

### How to use this plan

- Read **High-level purpose** for the scientific idea.
- Read **Frozen scientific design** for exactly what will be tested.
- Use **Construction workflow** as the step-by-step work order.
- Use **Phase 13 C1 gate** to decide what the result means.
- Use **Implementation checklist** to track execution.

The immediate first action is Task 1: approve and freeze the definitions. It is
not a new KDA run.

## High-level purpose

### The question in everyday language

AD may be associated with higher expression of a respiratory program in one
group and lower expression of the same program in another group. The existing
analyses show patterns like this descriptively, but they do not yet directly
test whether the two AD effects differ when donors are treated as the sample.

Phase 13 supplies that missing direct test.

### Why the direct comparison is necessary

The following pattern is not enough:

```text
Group A: AD versus NCI is statistically significant.
Group B: AD versus NCI is not statistically significant.
```

That pattern can occur simply because Group B has fewer donors or more
donor-to-donor variation.

The required C1 question is:

```text
(AD minus NCI in Group A) minus (AD minus NCI in Group B)
```

This is often called an **interaction** or a **difference-of-differences**.
Throughout this plan, “direct modifier test” means this exact comparison.

### Why programs are tested

A respiratory program is a prespecified group of genes that perform related
mitochondrial jobs. A program is also called a gene module.

Testing a program makes sense because:

- respiration requires many genes working together;
- one gene can change by chance;
- a coordinated program can be real even when no single gene has a very large
  change; and
- a donor-level program score gives an understandable effect size.

The full beginner explanation is in
[C1 donor-level module workflow](c1_donor_module_workflow_explained.md).
The exact proposed genes are in
[C1 respiratory module gene lists](c1_four_respiratory_module_gene_lists.md).

### What a successful Phase 13 result would permit

If a prespecified test passes every C1 rule, an allowed result is:

> In ROSMAP broad excitatory neurons, APOE group modified the AD-associated
> nuclear OXPHOS expression difference; the female e4 effect was more negative
> than the female e33 effect.

The sentence must name:

- the dataset;
- the cell context;
- whether sex or APOE was the modifier;
- the exact comparison;
- the exact module; and
- the direction.

The result must be called **internally supported in ROSMAP**, not independently
replicated.

Phase 13 alone does not permit:

> APOE causes mitochondrial failure in a specific neuronal cell type.

## Relationship to preceding phases

Phase 13 reuses validated data-construction work but performs new inference.

| Source | Frozen Phase 13 use |
|---|---|
| Phase 02 | The 276-donor analytic cohort and diagnosis, recorded sex, APOE, age at death, and postmortem interval |
| Phase 03 | Gene identifiers, stable gene annotations, mtDNA genes, and the frozen MitoCarta 3.0 source |
| Phase 04 | Per-nucleus QC metadata and auditable barcode-to-donor assignments |
| Phase 07 | Raw-count donor-by-fine-cell-type pseudobulk bundles, sample tables, and count-conservation checks |
| Phase 08 | Discovery context only; it is not a Phase 13 inferential input |
| Phase 09 | Supporting identifier audit only; Phase 13 must freeze its own module-to-assay mapping |
| Phases 10–11 | Discovery context only; similarity scores and pathway results are not C1 tests |
| Phase 12 | Not used; KDA is neither needed nor allowed for C1 |

### Required Phase 07 prerequisite

The current local checkout contains validated Phase 07 Vasculature smoke-test
files. It does not contain the required Minerva-production Phase 07 bundles for
all nine source RDS inputs used to build the seven broad production contexts.

Before Phase 13 production:

1. check whether those Phase 07 bundles exist and are
   `validated_complete` on Minerva;
2. sync their manifests and status files if they exist; or
3. run the frozen Phase 07 pseudobulk task for the nine required RDS inputs if
   they do not exist.

Phase 13 must not silently substitute Phase 08 cell-level normalized values for
missing Phase 07 raw-count pseudobulk.

### Discovery results and confirmation

Earlier same-cohort results motivated the four modules and seven comparisons.
They do not count as independent confirmation because they use the same
ROSMAP donors.

The new Phase 13 definitions must be frozen before inspecting the new
donor-level modifier results. Any later change is a documented exploratory
analysis with a new analysis profile, not a replacement for the frozen test.

## Plain-language map of the workflow

```text
Phase 07 raw-count profiles for fine cell types
                         |
                         v
Add fine types from the same donor into 7 broad classes
                         |
                         v
Normalize all genes, not only mitochondrial genes
                         |
              +----------+----------+
              |                     |
              v                     v
   Fit gene-level direct       Make 4 scores for
     modifier models             every donor
              |                     |
              v                     v
   Correlation-aware gene-     Directly compare
       set test (camera)       AD effects on scores
              |                     |
              +----------+----------+
                         |
                         v
      Bootstrap, leave-one-donor-out, and QC checks
                         |
                         v
          Apply the frozen C1 decision rules
```

Each donor remains a separate observation after the first aggregation step.
“Add” never means combining different donors.

## Frozen scientific design

### Unit of analysis

The independent biological sample is:

```text
one donor × one broad cell class
```

The profile contains raw counts for every usable gene.

Nuclei from the same donor and broad class are repeated measurements from the
same person. Their counts are added. Different donors stay in separate
columns.

### Primary broad cell contexts

Phase 13 includes all seven broad cell contexts available from the nine source
RDS inputs:

| `context_id` | Plain name | Phase 07 source RDS IDs | Construction |
|---|---|---|---|
| `astrocytes` | Astrocytes | `astrocytes` | Sum all astrocyte fine-type profiles for each donor |
| `excitatory_neurons` | Excitatory neurons | `excitatory_set1`, `excitatory_set2`, `excitatory_set3` | Sum all nonoverlapping excitatory fine-type profiles for each donor |
| `inhibitory_neurons` | Inhibitory neurons | `inhibitory` | Sum all inhibitory fine-type profiles for each donor |
| `immune_cells` | Immune cells | `immune` | Sum all immune fine-type profiles for each donor |
| `opcs` | Oligodendrocyte precursor cells | `opcs` | Sum all OPC fine-type profiles for each donor |
| `oligodendrocytes` | Oligodendrocytes | `oligodendrocytes` | Sum all oligodendrocyte fine-type profiles for each donor |
| `vasculature` | Vasculature cells | `vasculature` | Sum all vascular fine-type profiles for each donor |

The broad class is formed before applying the broad-class nucleus threshold.
A donor with two fine profiles containing 12 and 15 nuclei has 27 nuclei in
the broad class and is eligible at the 20-nucleus threshold.

Do not discard a fine profile merely because it has fewer than 20 nuclei before
forming the broad sum.

### Why broad classes are primary

Broad classes retain more donors and more counts than individual fine cell
types. That gives a more precise first test of C1. Including all seven available
broad lineages prevents the confirmatory scope from being restricted to
astrocytes and neurons without a prespecified biological reason.

A broad-class result does not prove that every fine subtype behaves identically.
A broad-class null result can also hide opposite fine-subtype effects. Those
questions are follow-up localization questions and must not change the primary
196-test family.

Phase 13 deliberately excludes an all-54-fine-type primary screen. Focused
fine-type localization may be planned after the locked Phase 13 decision.

### Twelve diagnosis, sex, and APOE groups

Every donor profile is assigned to one of twelve groups:

| Group ID | Diagnosis | Recorded sex | APOE group |
|---|---|---|---|
| `NCI__Female__e2` | NCI | Female | e2 |
| `AD__Female__e2` | AD | Female | e2 |
| `NCI__Female__e33` | NCI | Female | e33 |
| `AD__Female__e33` | AD | Female | e33 |
| `NCI__Female__e4` | NCI | Female | e4 |
| `AD__Female__e4` | AD | Female | e4 |
| `NCI__Male__e2` | NCI | Male | e2 |
| `AD__Male__e2` | AD | Male | e2 |
| `NCI__Male__e33` | NCI | Male | e33 |
| `AD__Male__e33` | AD | Male | e33 |
| `NCI__Male__e4` | NCI | Male | e4 |
| `AD__Male__e4` | AD | Male | e4 |

Here, e33 means APOE ε3/ε3. The e2 and e4 group definitions must be inherited
exactly from Phase 02; Phase 13 must not reclassify genotypes.

NCI means the comparison group labeled no cognitive impairment. It does not
mean pathology-free or biologically normal.

### Definition of an AD effect

For sex `s`, APOE group `a`, cell context `c`, and outcome `Y`:

```text
Delta(s, a, c) =
    adjusted mean Y in AD donors
    minus
    adjusted mean Y in NCI donors
```

The outcome can be one gene or one donor module score.

Positive Delta means higher expression in AD. Negative Delta means lower
expression in AD.

### Seven direct modifier contrasts

The seven comparisons are inherited from the validated Phase 07 contrast
logic. Every comparison is two-sided.

| Order | `contrast_id` | Exact comparison | Positive estimate means |
|---:|---|---|---|
| 1 | `sex_F_minus_M__e2` | Delta(Female,e2) − Delta(Male,e2) | AD effect is more positive, or less negative, in females |
| 2 | `sex_F_minus_M__e33` | Delta(Female,e33) − Delta(Male,e33) | AD effect is more positive, or less negative, in females |
| 3 | `sex_F_minus_M__e4` | Delta(Female,e4) − Delta(Male,e4) | AD effect is more positive, or less negative, in females |
| 4 | `apoe_e2_minus_e33__Female` | Delta(Female,e2) − Delta(Female,e33) | AD effect is more positive, or less negative, in female e2 |
| 5 | `apoe_e2_minus_e33__Male` | Delta(Male,e2) − Delta(Male,e33) | AD effect is more positive, or less negative, in male e2 |
| 6 | `apoe_e4_minus_e33__Female` | Delta(Female,e4) − Delta(Female,e33) | AD effect is more positive, or less negative, in female e4 |
| 7 | `apoe_e4_minus_e33__Male` | Delta(Male,e4) − Delta(Male,e33) | AD effect is more positive, or less negative, in male e4 |

For example, the coefficient vector for sex within e2 is:

```text
AD__Female__e2   +1
NCI__Female__e2  -1
AD__Male__e2     -1
NCI__Male__e2    +1
```

The coefficient vector for female e4 versus female e33 is:

```text
AD__Female__e4    +1
NCI__Female__e4   -1
AD__Female__e33   -1
NCI__Female__e33  +1
```

Every planned contrast must be verified with a small hand-calculated example.

### Planned primary grid

The complete primary grid is:

```text
7 broad cell contexts
× 7 direct modifier contrasts
× 4 frozen mitochondrial modules
= 196 planned tests
```

All 196 rows must be written to the test manifest before eligibility filtering
or model fitting.

An unavailable test remains in the result with a reason. It is never silently
removed.

### Four frozen mitochondrial modules

| `module_id` | Plain-language job | Reference size | Role in C1 |
|---|---|---:|---|
| `mtdna_oxphos_13` | Thirteen mtDNA genes that encode parts of respiratory complexes I, III, IV, and V | 13 | Direct respiratory module |
| `nuclear_oxphos_structural_86` | Nuclear genes whose proteins form respiratory complexes I–V | 86 | Direct respiratory module |
| `mitochondrial_translation_155` | Machinery that makes the 13 mtDNA-encoded proteins | 155 | Respiration-supporting module |
| `mib_micos_inner_membrane_19` | Proteins that organize the mitochondrial inner membrane and cristae | 19 | Respiration-supporting module |

The exact proposed lists and biological explanation are in
[C1 respiratory module gene lists](c1_four_respiratory_module_gene_lists.md).

The approved lists must also be copied into the machine-readable file:

```text
config/phase13_respiratory_modules.tsv
```

That file, not prose or a newly downloaded resource, is the production source
of truth.

The membership key is:

```text
module_id + frozen_gene_symbol
```

The expected membership count is:

```text
13 + 86 + 155 + 19 = 273 module-gene membership rows
```

Genes may occur in more than one module. The membrane module shares
`ATP5MD`, `ATP5ME`, and `ATP5MG` with nuclear OXPHOS. This overlap must be
recorded; the modules must not be described as four independent confirmations.

### Module roles and allowed wording

Only `mtdna_oxphos_13` and `nuclear_oxphos_structural_86` can by themselves
support the main C1 wording about an AD-associated respiratory or OXPHOS
expression program.

If only `mitochondrial_translation_155` passes, the permitted statement is
about a mitochondrial-translation expression program.

If only `mib_micos_inner_membrane_19` passes, the permitted statement is about
inner-membrane-organization expression.

Neither supporting module can be relabeled “OXPHOS” after the results.

### Identifier rules

The module file must contain:

- frozen source symbol;
- current approved symbol;
- stable Ensembl identifier;
- assay feature identifier;
- module membership;
- frozen omission category or categories;
- source and version;
- inclusion reason;
- overlap with other Phase 13 modules; and
- mapping status.

Blocking identifier rules include:

- `MRPL13` is included in mitochondrial translation;
- the distinct cytosolic gene `RPL13` is not substituted for `MRPL13`;
- the loose Phase 03 alias that associates `RPL13` with `MRPL13` is not used;
- old and current symbols are stored for
  `ATP5MD/ATP5MK`, `ATP5MPL/ATP5MJ`, `NDUFA4/COXFA4`,
  `C12orf65/MTRFR`, `MRPS36/KGD4`, `MINOS1/MICOS10`, and
  `C19orf70/MICOS13`;
- one assay feature cannot be counted twice in one module; and
- the 86-gene nuclear module contains no mtDNA gene and excludes
  `ATP5IF1`, `CYCS`, `HCCS`, and assembly factors.

### Module coverage

Coverage is evaluated separately in each broad cell context after the
full-transcriptome expression filter.

A module's final admitted genes must have one unique assay match, pass the
context-specific expression filter, and have a finite, nonzero NCI reference
standard deviation.

A module is testable only when:

```text
admitted module genes / frozen module genes >= 0.70
AND admitted module genes >= 5
```

The mtDNA module also requires:

```text
admitted mtDNA genes >= 10 of 13
```

Genes with no assay match, genes removed by the expression filter, and genes
with zero NCI reference variance are reported separately.

The following counts must be saved:

```text
reference genes
measured genes
genes passing the expression filter
genes with nonzero NCI standard deviation
genes used in the score
```

Apply coverage after zero-variance removal. Coverage failure gives
`not_testable_module_coverage`; it is not a biological null result. Use the
same admitted module index for the donor score and matching `camera` test.

### Donor and nucleus eligibility

Eligibility is applied separately in every broad cell context.

Primary profile threshold:

```text
at least 20 retained nuclei for the donor × broad cell class
```

Sensitivity threshold:

```text
at least 50 retained nuclei for the donor × broad cell class
```

For one direct contrast:

- fewer than 5 unique donors in any of its four required groups means
  `not_testable_low_donor_count`;
- 5–9 donors in any required group permits estimation but the result is
  `provisional_low_power`;
- at least 10 donors in every required group is required for an internally
  confirmatory Phase 13 result.

The known cohort-wide counts before broad-cell eligibility are:

| Group | NCI donors | AD donors |
|---|---:|---:|
| Female e2 | 17 | 8 |
| Female e33 | 45 | 37 |
| Female e4 | 11 | 26 |
| Male e2 | 6 | 7 |
| Male e33 | 53 | 29 |
| Male e4 | 10 | 27 |

These are an upper bound. A broad cell context can retain fewer donors after
the 20-nucleus rule.

Therefore, all e2 direct contrasts are expected to be estimable but cannot
meet the 10-donor internal-confirmation rule. A large e2 estimate remains
provisional unless a later independent dataset directly replicates it.

### Covariates

The primary models adjust for:

- age at death; and
- postmortem interval, or PMI; and
- ROS versus MAP parent study.

The exact stored variables are:

```text
age_death_scaled
pmi_scaled
study
```

Use the Phase 02 analytic-cohort scaling. Do not recalculate scaling separately
inside sex, APOE, diagnosis, or cell groups.

`study` is required because ROS and MAP membership is not balanced equally
across all 12 groups. Encode it as one frozen categorical model term, verify
both levels and full design rank, and save the group-by-study eligibility
table.

Percent mitochondrial reads is not a primary covariate because it can reflect
both technical quality and the biology being studied. It is added only in a
prespecified sensitivity analysis.

Unavailable batch or RNA-quality fields must not be invented. If a new
covariate is proposed, its availability and missingness must be audited before
results are opened and the change must create a new analysis profile.

### All-gene normalization

Every donor profile must retain the complete usable transcriptome. Phase 13
must not build, normalize, or model a count matrix containing only the 273
module memberships.

For each broad cell context:

1. construct an edgeR `DGEList` from all-gene raw counts;
2. create the frozen 12-group-plus-covariate design;
3. remove genes with too little information using `filterByExpr`;
4. reset library sizes after filtering;
5. calculate TMM normalization factors; and
6. calculate log counts per million, or logCPM, with frozen
   `prior.count = 2`.

TMM adjusts libraries for sequencing depth and composition. logCPM puts donor
expression values on a comparable, continuous scale.

The prior count is a small value used to prevent the logarithm of zero. It is
not two observed reads added to the raw data.

All module scores, NCI reference values, and sensitivity scores use the saved
full-transcriptome TMM/logCPM bundle. The same tested-gene set is used for the
gene model and the matching `camera` test.

### Supporting gene-level model

For each broad cell context, fit a robust edgeR quasi-likelihood count model:

```text
~ 0
  + diagnosis_sex_APOE_group
  + age_death_scaled
  + pmi_scaled
  + study
```

Required implementation steps are:

```r
y <- edgeR::DGEList(counts)
keep <- edgeR::filterByExpr(y, design)
y <- y[keep, , keep.lib.sizes = FALSE]
y <- edgeR::calcNormFactors(y, method = "TMM")
y <- edgeR::estimateDisp(y, design, robust = TRUE)
fit <- edgeR::glmQLFit(y, design, robust = TRUE)
```

Test all seven direct modifier vectors for every tested gene.

Also save the six within-stratum AD-minus-NCI effects for interpretation and
plotting. A within-stratum effect is descriptive support; it cannot replace
the direct modifier contrast.

The gene-level results must include:

- log2 fold-change difference-of-differences;
- standard error and 95% confidence interval;
- quasi-likelihood F statistic;
- raw P value;
- within-context-and-contrast BH q value;
- exact tested background;
- donor and nucleus counts for every required group;
- design rank and residual degrees of freedom;
- TMM factors and dispersion diagnostics; and
- model status and failure reason.

The current Phase 07 code reconstructs a one-degree-of-freedom interval from
the F statistic. Phase 13 must audit that calculation. The reported claim
interval must come from a documented contrast covariance calculation or the
donor bootstrap; an undocumented approximation is not acceptable.

Individual DEGs do not pass C1 by themselves. They show which genes contribute
to a program-level result.

### Primary donor module score

A module score turns the expression of many related genes into one value for
one donor.

Scores are constructed separately in each broad cell context.

#### Step 1: create an NCI reference for every admitted gene

For admitted gene `g` in cell context `c`, use all primary-eligible NCI donors
from all sex/APOE groups in that context:

```text
mu(g,c) = mean NCI logCPM
sd(g,c) = standard deviation among NCI logCPM values
```

“NCI reference” means only that these parameters are estimated in the NCI
comparison group. It does not imply that the donors are pathology-free.

Exclude and report a gene if `sd(g,c) = 0`.

#### Step 2: standardize every donor-gene value

For donor `d`:

```text
z(d,g,c) =
    [logCPM(d,g,c) - mu(g,c)]
    / sd(g,c)
```

This prevents very highly expressed genes from automatically dominating the
score.

#### Step 3: average genes with equal weight

For module `m`:

```text
raw_mean_z(d,m,c) =
    mean of z(d,g,c) over admitted genes g in module m
```

Every admitted gene receives equal weight.

#### Step 4: put module effects on one interpretable scale

Calculate the standard deviation of `raw_mean_z` among the same eligible NCI
donors:

```text
module_sd_NCI(m,c) = SD of raw_mean_z among NCI donors

module_mean_NCI(m,c) = mean raw_mean_z among NCI donors

standardized_score(d,m,c) =
    [raw_mean_z(d,m,c) - module_mean_NCI(m,c)]
    / module_sd_NCI(m,c)
```

The pooled NCI average is exactly zero apart from rounding. One score unit is
one NCI donor-level module-score standard deviation in that cell context.

Both `raw_mean_z` and `standardized_score` must be saved. The standardized
score is the primary outcome for the C1 module model.

If `module_sd_NCI` is zero or not finite, that module-context is not testable.

### Primary donor module model

For each context and module, fit:

```text
standardized_score
    ~ 0
      + diagnosis_sex_APOE_group
      + age_death_scaled
      + pmi_scaled
      + study
```

Use ordinary least squares with an HC3 heteroskedasticity-robust covariance
matrix. HC3 reduces reliance on an assumption that every donor group has the
same residual variance.

Use `sandwich::vcovHC(fit, type = "HC3")` with the package version in
`renv.lock`. For contrast vector `c` and fitted coefficients `beta`:

```text
estimate = c' beta
SE = sqrt(c' V_HC3 c)
df = number of fitted donor profiles - rank(design)
t = estimate / SE
P = 2 × Pr[T(df) >= absolute t]
95% CI = estimate ± t_(0.975,df) × SE
```

`sandwich` is not currently present as a locked package. Add and pin it in
`renv.lock` before execution. Do not switch covariance type, reference
distribution, degrees of freedom, or interval formula after seeing results.

Apply the same seven contrast vectors used by the gene model.

For each of the six sex/APOE strata, also save the adjusted AD-minus-NCI module
effect. These values explain the direct comparison but are not separate C1
tests.

### Alternative PC1 score

One scoring formula should not determine the conclusion.

The required alternative is the first principal component, called PC1:

1. use the same admitted gene-by-donor standardized matrix;
2. train the principal-component loadings using NCI donors only;
3. project all NCI and AD donors onto those frozen loadings;
4. subtract the pooled-NCI PC1 mean and divide by the pooled-NCI PC1 standard
   deviation;
5. orient the sign so PC1 correlates positively with the primary mean-z score
   among NCI donors;
6. use a deterministic gene-order tie-break if the NCI correlation is exactly
   zero; and
7. fit the same donor model and seven contrasts.

PC1 summarizes the largest shared pattern across module genes. Its sign is
mathematically arbitrary, so deterministic orientation is necessary.

For each context/module, save:

- loadings;
- variance explained by PC1;
- NCI mean and standard deviation used to scale PC1;
- NCI-only correlation between PC1 and mean-z score; and
- modifier estimates from both score definitions.

Flag module reliability when the NCI-only value is:

```text
absolute correlation(mean-z, oriented PC1) < 0.70
```

PC1 is a sensitivity analysis. It cannot replace a failed primary mean-z test.

### Correlation-aware gene-set test

The module score asks whether the average donor score has a direct modifier
effect.

A second method asks whether the module genes are unusually shifted compared
with the full tested transcriptome while allowing genes in one module to be
correlated.

Use limma-voom followed by `camera`:

1. use the same all-gene filtered count matrix and primary design;
2. calculate voom expression values and precision weights;
3. run each of the seven direct contrasts;
4. test all four frozen modules against the matching tested-gene background;
5. use the same final admitted genes used by the donor score;
6. use `allow.neg.cor = FALSE`;
7. calculate inter-gene correlation explicitly with the frozen limma method,
   pass that numeric value to `camera`, and save it; and
8. save the enrichment direction, raw P value, correlation, module coverage,
   and background size.

In plain language, `camera` asks:

> Are genes in this module collectively closer to the top or bottom of the
> direct modifier ranking than other tested genes?

The module-score and `camera` tests use the same donors and are not independent
replications. They test different null hypotheses. The score asks whether the
module changes between groups. `camera` asks the stricter question of whether
the module shifts more than the rest of the transcriptome. Compatible
`camera` direction is required for C1. `camera` q ≤ 0.05 is labeled extra
competitive gene-set support, not a basic C1 requirement.

### Multiple-testing correction

Testing many hypotheses increases the chance of a small P value by accident.
The Benjamini–Hochberg procedure, abbreviated BH, controls the expected false
discovery rate within a frozen family of tests.

Phase 13 has two primary families:

```text
Family M13-score:
    7 contexts × 7 contrasts × 4 modules = 196 module-score P values

Family M13-camera:
    7 contexts × 7 contrasts × 4 modules = 196 camera P values
```

Apply BH separately to the testable P values in these two families. Preserve
all 196 structural rows. Untestable rows have `p = NA` and `q = NA`.

Gene-level BH is separate for each context × contrast transcriptome-wide
result. It is supporting evidence and is not mixed into either 196-test module
family.

Within-stratum AD effects, PC1, the 50-nucleus analysis, QC-adjusted models,
and leave-one-gene/complex analyses are not new primary families. They are
descriptive or sensitivity outputs and cannot rescue a failed primary row.

### Smallest effect considered meaningful

A tiny difference can have a small P value without being biologically useful.
Phase 13 therefore freezes a smallest effect size of interest, abbreviated
SESOI.

Proposed Phase 13 value:

```text
SESOI = 0.25 NCI module-score standard deviations
```

This is a transparent project decision, not a universal biological constant.
The professor must approve it before results are opened.

A result meets the primary practical-effect rule when:

```text
absolute modifier estimate >= 0.25
AND the model-based 95% confidence interval excludes 0
```

This rule says the point estimate is at least 0.25 and the data support a
nonzero effect. It does **not** claim that the entire confidence interval lies
beyond 0.25. That stronger minimum-effect claim is not made.

A precise result supports practical equivalence to zero only when its entire
95% interval lies inside:

```text
[-0.25, +0.25]
```

If the interval crosses zero and also extends outside that range, the result is
uncertain rather than proof of no effect.

### Stability analyses

Every eligible one of the 196 primary rows receives the same prespecified
stability analyses. Stability is not run only on attractive results.

#### A. Stratified donor bootstrap

Run 1,000 production repetitions.

Run bootstrap sampling separately for each broad context, because ≥20-nucleus
eligibility is context-specific. In each repetition:

1. sample from that context's primary-eligible donor pool with replacement
   within each of the 12 diagnosis/sex/APOE groups;
2. give repeated draws unique analysis-column IDs while retaining the original
   donor ID in provenance;
3. never combine or compare bootstrap donors across contexts;
4. keep the full-data admitted module genes fixed;
5. never resample nuclei as independent donors;
6. rebuild TMM normalization;
7. recalculate NCI gene means, gene SDs, module mean, and module SD;
8. recalculate module scores; and
9. refit the module models and contrasts.

Save every replicate estimate and failure reason.

Summaries include:

- median bootstrap estimate;
- 2.5th and 97.5th percentiles;
- fraction with the same sign as the primary estimate; and
- fraction of successful repetitions.

Required directional stability:

```text
at least 80% of successful bootstrap estimates have the primary sign
```

At least 950 of 1,000 repetitions must fit successfully for the bootstrap
component to be valid.

#### B. Leave one donor out

For every unique donor:

1. remove that donor from every broad cell context;
2. keep the full-data admitted module genes fixed;
3. rebuild normalization and NCI references;
4. refit every eligible module model; and
5. save all contrast estimates.

A sign reversal occurs when:

```text
primary estimate × leave-one-donor-out estimate < 0
```

A gate-passing result requires zero sign reversals.

Also report the donor producing:

- the largest absolute change;
- the smallest estimate;
- the largest estimate; and
- any model failure.

#### C. Stricter 50-nucleus threshold

Repeat the complete module-score analysis using donor-context profiles with at
least 50 nuclei.

When estimable, the result agrees when:

```text
same direction as primary
AND absolute sensitivity estimate >= 0.50 × absolute primary estimate
```

If the stricter threshold leaves fewer than five donors in a required group,
record `not_testable_threshold50`. Do not call it a contradictory null.

#### D. Group-size-balanced resampling

Large differences in group size can make one side of a comparison much more
precise.

For each `context × contrast` row, run 1,000 repetitions using that context's
eligible donors:

1. find the smallest donor count among its four required groups;
2. sample that number without replacement from every required group;
3. retain all primary-eligible donors from the other eight groups in that
   context;
4. keep admitted module genes fixed, rebuild TMM and NCI references, and fit
   the full 12-group model; and
5. record the same four-term contrast estimate.

Require at least 80% of successful balanced estimates to have the primary
direction. At least 950 of 1,000 repetitions must fit successfully. This check
is especially important for e2.

#### E. Mitochondrial-QC covariate sensitivity

As an artifact diagnostic, repeat the module model after adding the
donor-context aggregate:

- mitochondrial read fraction; and
- robust-QC-flag fraction.

These are sensitivity covariates, not assumed confounders. Percent
mitochondrial reads is mathematically related to the mtDNA module itself, so
the percent-mt-adjusted mtDNA result is reported but never required to retain
50% magnitude or pass the C1 gate.

For nuclear modules, save whether the covariate-adjusted result has the same
sign and at least 50% of the primary magnitude, but keep it as a sensitivity
label rather than a veto of the main result.

Also repeat after excluding profiles that meet the frozen severe-QC rule. The
severe-QC rule must be based on Phase 04 fields and written in the configuration
before effects are viewed. Freeze:

```text
severe-QC profile =
    robust_flagged_nuclei / total_retained_nuclei >= 0.50
```

This exclusion sensitivity must retain the primary direction for a supported
row. Report how many donors/groups are lost; if the model becomes untestable,
the support decision is inconclusive.

#### F. Gene-concentration sensitivity

A small set can appear positive because one gene dominates.

For the 13-gene mtDNA and 19-gene membrane modules:

- remove one admitted gene at a time;
- recalculate the score; and
- refit the same contrast.

For the 86-gene nuclear OXPHOS module:

- leave out one respiratory complex at a time.

For the 155-gene translation module:

- leave out each frozen category in turn:
  mitochondrial ribosome, ribosome assembly, translation factors,
  mt-tRNA synthetases, fMet processing, and the nine parent-only genes.

`MRPL58` and `PTCD3` belong to two source child labels. When either relevant
category is omitted, remove that gene once and record the overlap.

Report the fraction of omissions retaining the primary sign and identify the
most influential gene, complex, or category.

For a supported row:

```text
zero omission sign reversals
AND at least 80% of omission estimates retain
    at least 50% of the primary absolute magnitude
```

This is a reliability gate, not a new P-value family.

### Deterministic randomization

Use:

```text
RNGkind("L'Ecuyer-CMRG")
```

Freeze a base seed in the Phase 13 configuration. Derive each repetition seed
from:

```text
base seed + stable analysis/test/repetition identifier
```

Do not derive seeds from worker number or completion order.

Sort contexts, donors, genes, contrasts, modules, and output rows explicitly
before calculation and writing.

### Phase 13 C1 gate

Technical completion and scientific support are different.

A technically correct run can finish with no supported biological result.

#### Gate for one context × contrast × module row

A row is `supported` only when all of the following are true:

1. all four required groups have at least 10 eligible donors;
2. the module passes the frozen coverage rules;
3. the primary module-score BH q value is at most 0.05;
4. the absolute standardized effect is at least 0.25 and its 95% interval
   excludes zero;
5. `camera` is testable and has the same biological direction; q ≤ 0.05 is
   separately labeled `competitive_gene_set_support`;
6. at least 80% of donor bootstraps retain the direction;
7. no leave-one-donor-out estimate reverses direction;
8. the mean-z and oriented-PC1 scores correlate by at least 0.70;
9. standardized PC1 and the 50-nucleus analysis retain the direction and at
   least 50% of the primary magnitude whenever estimable;
10. at least 80% of balanced resamples retain the direction; and
11. the frozen gene/complex/category-omission rule passes; and
12. the frozen severe-QC-exclusion result retains the direction and no blocking
    technical or provenance check fails.

If a required sensitivity cannot be estimated because of data availability,
the evidence table records it explicitly. It cannot be silently treated as a
pass. The locked review decides `inconclusive` rather than `supported` when a
missing mandatory check prevents a reliable decision.

#### Scientific status for one row

Use exactly one of:

| Status | Meaning |
|---|---|
| `supported` | Every required scientific and stability rule passed |
| `provisional_low_power` | The primary pattern is present but at least one required group has 5–9 donors |
| `statistically_detectable_but_small` | q threshold passed but the effect did not meet the 0.25 SESOI |
| `not_supported_precise_null` | The full 95% interval lies inside [−0.25,+0.25] |
| `inconclusive` | The interval or stability evidence is too uncertain for support or a precise null |
| `not_testable` | Donor count, module coverage, design rank, or required data make the test impossible |

A row with q greater than 0.05 is not automatically a precise null.

Apply statuses in this order:

1. `not_testable` if the model cannot be estimated;
2. `provisional_low_power` only when all non-donor-count support rules pass
   but at least one required group has 5–9 donors;
3. `supported` when every rule, including ≥10 donors, passes;
4. `statistically_detectable_but_small` when the score q passes and the
   nonzero interval rule passes but the point estimate is below 0.25;
5. `not_supported_precise_null` when the full interval lies inside the SESOI
   range; and
6. `inconclusive` otherwise.

Also save separate Boolean fields such as `effect_meets_sesoi` and
`interval_inside_sesoi` so one label never hides the underlying evidence.

#### Overall C1 decision

The primary C1 respiratory claim uses the two direct respiratory modules only:

```text
mtdna_oxphos_13
nuclear_oxphos_structural_86
```

Overall labels are:

| Overall label | Rule |
|---|---|
| `supported_both` | At least one confirmatory sex row and one confirmatory APOE row pass in a direct respiratory module |
| `supported_sex_only` | At least one confirmatory sex row passes, but no APOE row passes |
| `supported_apoe_only` | At least one confirmatory APOE row passes, but no sex row passes |
| `not_supported` | All internally confirmable direct-respiratory rows are precise nulls and none pass |
| `inconclusive` | No row passes and the available intervals or stability checks remain too uncertain |
| `not_testable` | No direct-respiratory row can be estimated adequately |

A translation- or membrane-only result is reported as a narrower secondary
finding and does not change the C1 respiratory label to supported.

If even one relevant internally confirmable direct-respiratory row is
inconclusive or lacks a mandatory stability result, the overall no-support
decision is `inconclusive` rather than `not_supported`.

The final claim wording must name only the rows that pass. One passing context
does not prove statistical cell-type specificity. Use:

> in the analyzed astrocyte context

or:

> in broad excitatory-neuron profiles

Do not use:

> specific to astrocytes

unless the separate Claim 2 between-cell-type test later passes.

### Deliberately excluded C1 extensions

Three analyses discussed in the wider research plan are not part of the Phase
13 C1 gate:

- **Nucleus-depth downsampling:** Phase 13 inherits donor pseudobulk counts and
  does not read raw nucleus count matrices. TMM handles library size, and the
  ≥20/≥50 analysis tests profile-eligibility sensitivity, but it does not prove
  invariance to exact equal nucleus depth. A true nucleus-depth experiment
  requires a separately approved raw-RDS analysis.
- **Expression-matched non-mitochondrial null sets:** these are required for a
  claim that mitochondrial change is selective or more profound than other
  biology. C1 only asks whether a frozen mitochondrial program has a direct
  modifier effect. `camera` provides transcriptome-relative context, but is
  not an expression/detection-matched null.
- **`fgseaMultilevel`:** Phase 13 freezes `camera` as its correlation-aware
  ranked gene-set method. An fgsea sensitivity may be a later supplement, but
  it cannot replace or rescue the donor module-score test.

These exclusions narrow what Phase 13 can claim. They are not silently treated
as completed checks.

## Inputs and dependencies

### Required inputs

| Source | Required production files | Blocking requirement |
|---|---|---|
| Phase 02 | `global_cohort_276.tsv`, nine source-specific cohort tables, `cohort_group_counts.tsv`, `cohort_status.tsv` | Status is `validated_complete`; donor metadata and the 276-donor definition match |
| Phase 03 | `annotation_status.tsv`, GENCODE table, mtDNA table, MitoCarta measured-gene table, frozen MitoCarta workbook | Status and workbook checksum validate |
| Phase 04 | `<rds_id>_cell_qc.tsv.gz`, status, and check tables for nine required RDS IDs | All nine statuses are `validated_complete` |
| Phase 07 | count RDS, sample table, conservation table, and status for nine required RDS IDs | Raw-count schema and conservation validate; status is `validated_complete` |
| Phase 13 | approved YAML and 273-row module-membership TSV | No required definition is missing or `TBD` |

The nine required source RDS IDs are:

```text
astrocytes
excitatory_set1
excitatory_set2
excitatory_set3
immune
inhibitory
opcs
oligodendrocytes
vasculature
```

Required donor fields are `projid`, diagnosis, recorded sex, APOE group,
`age_death_scaled`, `pmi_scaled`, `study`, and cohort inclusion. Read `projid`
as character.

Expected Phase 07 files are under:

```text
results/minerva_production/07_pseudobulk/
```

The exact filename stems must come from validated manifests. If any required
Phase 07 bundle is missing, stop Phase 13 and run the existing Phase 07
pseudobulk prerequisite. Never substitute Phase 08 normalized cell values.

The frozen MitoCarta workbook is:

```text
data/reference/Human.MitoCarta3.0.xls
```

The reliable normalized pathway-membership table is:

```text
results/minerva_production/11_pathway/pathway_membership_long.tsv.gz
```

It may be used to construct and audit the module TSV before freezing.
Production reads the frozen Phase 13 module TSV, not the Phase 11 result table.
Do not use the older Phase 03 pathway `gene_count` field; its delimiter parser
can report a comma-separated gene list incorrectly.

### Required configuration and software

Create and freeze:

```text
config/phase13_respiratory_modifier.yml
config/phase13_respiratory_modules.tsv
```

The YAML must contain the contexts, groups, contrasts, modules, thresholds,
formulas, FDR families, SESOI, repetitions, sensitivity rules, base seed,
input/output roots, schema version, and pilot flag.

Required R packages are:

```text
yaml, data.table, Matrix, edgeR, limma, sandwich, digest
```

Use versions recorded in `renv.lock`. Add and pin `sandwich` explicitly before
execution.

### Explicit non-inputs

The scientific Phase 13 script must not read Phase 08 DEG results, Phase 10
similarity scores, Phase 11 result tables, Phase 12 KDA results, or figure
outputs. They motivated the hypothesis but do not define the confirmatory
runtime tests.

## Construction workflow

Each task below states what is needed, what is done, and what is produced.

### Task 1: freeze definitions

**Why:** prevent outcome-driven changes.

**Inputs:** approved plan, module source, Phase 02 group definitions, and
professor-approved SESOI/gate rules.

**Steps:**

1. write the YAML and 273 module-membership rows;
2. map each module gene to one stable assay feature;
3. hand-check `MRPL13` versus `RPL13`;
4. write seven contexts and seven coefficient vectors;
5. record the two 196-test FDR families;
6. record approval and calculate hashes; and
7. set `definitions_frozen = TRUE`.

**Outputs:** analysis, context, contrast, four-row module, and 273-row
module-membership manifests.

**Ready when:** no field is `TBD` and every expected count validates.

### Task 2: validate inherited inputs

**Why:** a downstream result cannot be stronger than its source data.

**Inputs:** Phase 02, 03, 04, and 07 bundles plus their status/check files.

**Steps:**

1. verify files, schemas, terminal statuses, and hashes;
2. confirm cohort metadata agree across sources;
3. confirm all nine matrices have identical ordered features;
4. prove the three excitatory barcode sets are pairwise disjoint;
5. verify count columns match sample rows;
6. reproduce Phase 07 count conservation; and
7. stop on any blocking failure.

**Outputs:** `respiratory_input_inventory.tsv`,
`respiratory_source_identity_checks.tsv`, and input checks.

### Task 3: build broad donor profiles

**Why:** donors are the independent samples; broad classes preserve more
donors and RNA counts.

**Inputs:** nine all-gene Phase 07 count bundles and sample metadata.

**Steps:**

1. keep cohort-included fine profiles even when they have fewer than 20 nuclei;
2. sum astrocyte fine profiles within donor;
3. align and sum all three disjoint excitatory sources within donor;
4. sum inhibitory fine profiles within donor;
5. sum immune fine profiles within donor;
6. sum OPC fine profiles within donor;
7. sum oligodendrocyte fine profiles within donor;
8. sum vascular fine profiles within donor;
9. aggregate nuclei, UMI, mitochondrial counts, and QC numerators;
10. attach one consistent donor metadata record;
11. apply ≥20 and ≥50 nuclei after broad aggregation; and
12. verify gene-wise and total-count conservation exactly.

**Outputs:** broad count RDS, one-row-per-donor/context sample table,
conservation table, and QC summary.

### Task 4: create the full test manifest

**Why:** unavailable or negative tests must remain visible.

**Inputs:** seven contexts, seven contrasts, four modules, donor counts, and
module mapping.

**Steps:**

1. create the complete Cartesian product;
2. assign `test_id = context_id::contrast_id::module_id`;
3. record four-group donor/nucleus counts at both thresholds;
4. record preliminary module coverage;
5. assign eligibility without looking at effect estimates; and
6. write exactly 196 production rows.

**Output:** `respiratory_test_manifest.tsv`.

### Task 5: normalize all genes and fit gene models

**Why:** full-transcriptome normalization is needed for valid scores and
gene-set backgrounds.

**Inputs:** broad all-gene counts, donor metadata, and contrasts.

**Steps:**

1. construct one edgeR object per context;
2. build and rank-check the 12-group-plus-age-plus-PMI-plus-study design;
3. run `filterByExpr`, TMM, robust dispersion, and robust QL fitting;
4. save TMM logCPM with `prior.count = 2`;
5. estimate six stratum AD effects and seven direct modifier effects;
6. apply gene-level BH within context/contrast; and
7. save diagnostics and exact tested backgrounds.

**Outputs:** expression bundle, gene stratum effects, gene interaction results,
and model diagnostics.

### Task 6: freeze coverage and calculate module scores

**Why:** the score must not change membership in response to the outcome.

**Inputs:** frozen modules, tested genes, NCI logCPM, and donor metadata.

**Steps:**

1. mark measured, filtered, zero-variance, admitted, and excluded genes;
2. apply coverage rules and freeze context-module membership;
3. calculate and save NCI gene means/SDs;
4. calculate raw mean-z and NCI-SD-standardized scores;
5. fit the HC3 score model and seven direct contrasts;
6. estimate the six stratum AD effects;
7. apply BH over the 196 score tests;
8. train and orient the NCI-only PC1 sensitivity; and
9. hand-reproduce selected scores and contrasts.

**Outputs:** coverage, NCI parameters, donor scores, PC1 loadings, stratum
effects, 196 score results, and reliability table.

### Task 7: run `camera`

**Why:** check program coherence without relying only on the mean-z formula.

**Inputs:** matching full-transcriptome voom data, design, contrasts, and module
indexes.

**Steps:**

1. verify sample and design order;
2. run four modules for every context/contrast;
3. retain direction, inter-gene correlation, set/background sizes, and P value;
4. preserve untestable rows;
5. apply BH over the separate 196-row family; and
6. compare direction with the score estimate.

**Output:** `respiratory_camera_results.tsv` with 196 rows.

### Task 8: run stability analyses

**Why:** detect dependence on one donor, one score, unequal group size, the
nucleus-eligibility threshold, or mitochondrial QC.

**Inputs:** frozen 196-row manifest, broad profiles, admitted modules, primary
results, and deterministic seeds.

**Steps:**

1. run 1,000 stratified whole-donor bootstraps;
2. leave every donor out once across all contexts;
3. run 1,000 four-group-balanced resamples;
4. repeat at the ≥50-nucleus threshold;
5. run the NCI-trained PC1 endpoint;
6. add frozen mitochondrial/QC covariates and severe-QC exclusion;
7. omit one gene, complex, or translation category at a time; and
8. save every fit/failure plus one 196-row summary.

**Outputs:** long stability replicates, 196-row stability summary, and module
reliability diagnostics.

### Task 9: apply the locked C1 gate

**Why:** the conclusion must follow written rules, not the best-looking plot.

**Inputs:** score, `camera`, stability, eligibility, coverage, and check tables.

**Steps:**

1. join all evidence by exact `test_id`;
2. calculate one Boolean field per gate rule;
3. assign row status without manual scoring;
4. separate sex, APOE, direct-respiratory, and supporting-module outcomes;
5. create exact allowed wording;
6. retain every provisional, inconclusive, null, and untestable row;
7. record any plan deviation; and
8. validate and publish the status last.

**Outputs:** gate decisions, claim summary, checks, artifacts, and status.

## Outputs and file contract

Final production root:

```text
results/minerva_production/13_respiratory_modifier/
```

| File | Required content |
|---|---|
| `respiratory_analysis_manifest.tsv` | One frozen analysis definition, approval, versions, thresholds, and hashes |
| `respiratory_cell_context_manifest.tsv` | Seven source-to-broad context rows |
| `respiratory_contrast_manifest.tsv` | Seven ordered comparisons with four groups and coefficients |
| `respiratory_module_manifest.tsv` | Four ordered module definitions, roles, sizes, sources, and coverage rules |
| `respiratory_module_members.tsv` | 273 module-gene membership rows and stable assay mappings |
| `respiratory_input_inventory.tsv` | All required input paths, statuses, schemas, and hashes |
| `respiratory_source_identity_checks.tsv` | Feature, barcode, donor, and cross-source checks |
| `respiratory_test_manifest.tsv` | Exactly 196 structural tests and eligibility |
| `respiratory_donor_samples.tsv.gz` | One donor/context row, group metadata, nuclei, UMI, and QC |
| `respiratory_pseudobulk_counts.rds` | Seven sparse all-gene raw-count matrices |
| `respiratory_count_conservation.tsv` | Source-to-broad gene and total-count checks |
| `respiratory_qc_summary.tsv` | Donor counts and QC by context/group/threshold |
| `respiratory_expression_bundle.rds` | Tested genes, TMM factors, logCPM, designs, and backgrounds |
| `respiratory_gene_stratum_effects.tsv.gz` | Six AD-minus-NCI effects per context/gene |
| `respiratory_gene_interaction_results.tsv.gz` | Seven direct effects per context/gene |
| `respiratory_gene_model_diagnostics.tsv` | Design, dispersion, TMM, sample, and fit diagnostics |
| `respiratory_module_coverage.tsv` | Reference/measured/tested/admitted/excluded counts and genes |
| `respiratory_nci_reference_parameters.tsv.gz` | Context/gene NCI mean and SD |
| `respiratory_donor_module_scores.tsv.gz` | Raw mean-z, standardized, and PC1 score per donor/context/module |
| `respiratory_pc1_loadings.tsv.gz` | NCI-trained loading per context/module/gene plus scaling and orientation |
| `respiratory_module_stratum_effects.tsv` | 7 × 4 × 6 = 168 adjusted stratum effects |
| `respiratory_module_results.tsv` | Exactly 196 primary score results |
| `respiratory_camera_results.tsv` | Exactly 196 `camera` results |
| `respiratory_module_reliability.tsv` | PC1 correlation/variance and omission diagnostics |
| `respiratory_stability_replicates.tsv.gz` | Long-form bootstrap, LOO, balance, threshold, QC, and omission fits |
| `respiratory_stability_summary.tsv` | Exactly 196 stability summaries |
| `respiratory_gate_decisions.tsv` | Exactly 196 component-by-component decisions |
| `respiratory_claim_summary.tsv` | Sex, APOE, overall, supporting, and provisional conclusions |
| `respiratory_stage_status.tsv` | Checkpoint dependencies, fingerprints, shard counts, times, and terminal stages |
| `respiratory_checks.tsv` | Blocking/nonblocking checks |
| `respiratory_artifacts.tsv` | Paths, schemas, rows, bytes, and content hashes |
| `respiratory_status.tsv` | One phase-level technical and scientific status row |

The four-row module manifest stores module order/ID/label/role, reference gene
count, source, coverage thresholds, mtDNA-specific minimum, and overlap policy.
The PC1 table stores context, module, gene/assay ID, loading, NCI training
count, scaling parameters, and orientation correlation. The stage table stores
stage order/ID, dependencies, analysis fingerprint, planned/completed/reused/
skipped/failed shards, start/finish time, and terminal status.

Key result fields include `test_id`, context, contrast, module, effect, robust
SE, 95% interval, P, family q, four group counts, coverage, result status, and
provenance. `respiratory_gate_decisions.tsv` must have one explicit column for
every gate requirement plus the exact permitted sentence. It stores
`camera_direction_compatible` and `camera_competitive_q_support` separately;
only the direction field belongs to the basic C1 gate.

Technical status and scientific conclusion remain separate:

```text
validation_status = validated_complete

scientific_decision =
    supported_both | supported_sex_only | supported_apoe_only |
    not_supported | inconclusive | not_testable |
    not_applicable_pilot
```

A negative or inconclusive biological result is not a technical failure.

Control-table schemas are frozen as:

```text
respiratory_checks.tsv:
schema_version, check_id, stage_id, scope_type, scope_id,
blocking, passed, observed, expected, details

respiratory_artifacts.tsv:
schema_version, artifact_role, artifact_id, path, bytes, records,
sha256, canonical_content_sha256, output_schema, validation_status

respiratory_status.tsv:
schema_version, execution_stage, execution_phase, backend, run_id,
stable_task_id, task_mode, scientific_script,
scientific_script_sha256, scientific_config_sha256,
module_manifest_sha256, pipeline_config_sha256,
execution_config_sha256, rds_manifest_sha256,
contexts, modules, module_memberships, modifier_contrasts,
planned_primary_tests, eligible_tests, not_testable_tests,
score_result_rows, camera_result_rows, bootstrap_repetitions,
balance_repetitions, supported_rows, scientific_decision,
failed_checks, artifact_manifest_sha256, validation_status,
git_revision, timestamp_utc
```

Every TSV begins with a frozen `schema_version` column. Every RDS stores
`schema_version` inside the object.

Temporary shards live only under the configured scratch directory. The final
directory is flat, complete, and published atomically.

Pilot and production publish the same declared filenames and schemas, with:

```text
local pilot: 1 context, 28 tests, 24 module-stratum rows
production:  7 contexts, 196 tests, 168 module-stratum rows
```

## Phase 13 end state: files added, modified, generated, and deleted

Phase 13 is finished only when the source-controlled implementation exists,
the local pilot and Minerva production bundles validate, and every one of the
196 production rows has a terminal scientific status. A positive biological
result is not required for technical completion.

### Source-controlled files added

These five files are new:

| File | End-state purpose |
|---|---|
| `config/phase13_respiratory_modifier.yml` | Frozen contexts, groups, seven contrasts, thresholds, formulas, FDR families, stability rules, seeds, and paths |
| `config/phase13_respiratory_modules.tsv` | Frozen 273 module-gene membership rows with identifiers, roles, and inclusion rules |
| `scripts/13_run_respiratory_modifier.R` | Global checkpointed implementation for input validation, broad aggregation, models, scores, `camera`, stability, gates, and atomic publication |
| `tests/test_phase13_respiratory_modifier.R` | Synthetic, unit, integration, and output-only validation tests |
| `docs/phase_13_repiratory_modifier/phase_13_respiratory_modifier_plan.md` | The approved scientific, implementation, execution, output, and completion contract |

### Existing source-controlled files modified

Only these four existing files are changed by the planned implementation:

| File | Required end-state change |
|---|---|
| `scripts/run_pipeline.R` | Register and dispatch the global `respiratory_modifier` task, resolve its Phase 13 configuration, and enforce its argument contract |
| `config/local_pilot.yml` | Add the Phase 13 scientific-config path and allow the `respiratory_modifier` task mode for the local pilot |
| `config/minerva_shared.yml` | Add the Phase 13 scientific-config path and allow the `respiratory_modifier` task mode for Minerva production |
| `renv.lock` | Add and pin the required `sandwich` package, which is not currently present as a locked package |

Other than the four integration and dependency files listed above, no existing
source-controlled file is modified. No Phase 00-12 validated result file is
modified in place. If implementation later proves that another tracked file
must change, that is a plan deviation and must be added to this inventory
before the production result is opened.

### Generated result directories

Execution creates two result bundles:

| Directory | End state |
|---|---|
| `results/local_pilot/13_respiratory_modifier/` | Nonfinal smoke-test bundle with 1 context, 28 structural tests, 24 module-stratum rows, and `validation_status = nonfinal_smoke_test` |
| `results/minerva_production/13_respiratory_modifier/` | Final flat production bundle with 7 contexts, 196 structural tests, 168 module-stratum rows, and `validation_status = validated_complete` |

Each bundle contains exactly the 32 declared filenames in the preceding
[Outputs and file contract](#outputs-and-file-contract) table. The independent
validator rejects missing files, undeclared files, and subdirectories. Temporary
checkpoint shards remain under the configured scratch root and are not part of
the final result bundle.

### Number of production result sets

Phase 13 production tests 196 distinct scientific hypotheses:

```text
7 broad cell contexts
x 7 direct sex/APOE contrasts
x 4 frozen modules/programs
= 196 planned result sets
```

The modifier breakdown is:

```text
sex contrasts:
    7 contexts x 3 sex contrasts x 4 modules/programs = 84

APOE contrasts:
    7 contexts x 4 APOE contrasts x 4 modules/programs = 112

total:
    84 + 112 = 196
```

Each of the 196 hypotheses receives several linked evidence and decision
outputs. These are repeated measurements of the same planned hypothesis, not
additional independent hypotheses:

| Production output | Required rows | Role |
|---|---:|---|
| `respiratory_module_results.tsv` | 196 | Primary donor module/program-score results |
| `respiratory_camera_results.tsv` | 196 | Supporting correlation-aware gene-set results |
| `respiratory_stability_summary.tsv` | 196 | Bootstrap, leave-one-donor-out, balance, threshold, QC, and omission summaries |
| `respiratory_gate_decisions.tsv` | 196 | Final component-by-component status and permitted wording for each hypothesis |
| `respiratory_module_stratum_effects.tsv` | 168 | Descriptive AD-minus-NCI effects for 7 contexts x 4 modules/programs x 6 sex/APOE strata |

The 168 stratum effects explain the seven direct difference-of-differences but
are not additional primary tests. Gene-level results provide supporting detail
and have data-dependent row counts because they cover every adequately measured
gene. Therefore, “196 result sets” refers specifically to the frozen
`context x contrast x module/program` scientific grid.

The production bundle ends with two separate conclusions:

```text
technical state:
    validation_status = validated_complete

scientific state:
    scientific_decision =
        supported_both | supported_sex_only | supported_apoe_only |
        not_supported | inconclusive | not_testable
```

Every one of the 196 planned rows ends with exactly one of the six frozen row
statuses—`supported`, `provisional_low_power`,
`statistically_detectable_but_small`, `not_supported_precise_null`,
`inconclusive`, or `not_testable`—plus its estimate, interval, q value, donor
counts, stability results, gate fields, permitted wording, and provenance.

### Files deleted

None. Phase 13 deletes no source-controlled file, raw input, Phase 00-12
artifact, or previously validated result bundle. A rerun builds in new scratch
space and cannot replace an existing validated Phase 13 production bundle until
the replacement independently validates.

### Required registration details

Use one global script with checkpointed internal functions for input
validation, broad aggregation, manifests, gene models, scoring, `camera`,
stability, gate review, and atomic publication.

Register:

```text
task_mode: respiratory_modifier
scope: global
stable_task_id: global:respiratory_modifier
output_schema: mitochondrial_respiratory_modifier_v1
```

Both environment YAML files must add:

```yaml
project:
  phase13_respiratory_modifier_config: config/phase13_respiratory_modifier.yml

scope:
  allowed_task_modes:
    - respiratory_modifier
```

In `scripts/run_pipeline.R`, add the registry row, task-specific Phase 13
config resolver, `implemented_global_modes` entry, and argument contract:

```text
config,execution-config,task-mode
```

The global task rejects `--rds-id`. If `--force` is supported, it must write
a replacement in new scratch space and leave an existing validated bundle
untouched until replacement validation passes.

Do not overwrite Phase 00–12 artifacts. Reuse Phase 07 logic without changing
its validated outputs.

## Local pilot

Use the validated local Vasculature Phase 07 bundle as one pseudo-broad
context. The pilot has:

```text
1 context × 7 contrasts × 4 modules = 28 structural rows
```

It validates code and schemas only. Add deterministic synthetic fixtures for a
known positive interaction, known null, coverage failure, zero-variance gene,
rank failure, influential donor, BH calculation, and PC1 orientation.

Planned commands:

```bash
cd /Users/rzhuang/Documents/VscodeProjects/alzheimer

Rscript tests/test_phase13_respiratory_modifier.R

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase respiratory_modifier \
  --dry-run

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase respiratory_modifier

Rscript tests/test_phase13_respiratory_modifier.R \
  --validate-output results/local_pilot/13_respiratory_modifier \
  --expected-contexts 1 --expected-tests 28 \
  --expected-stratum-rows 24 \
  --expected-status nonfinal_smoke_test
```

Expected status:

```text
validation_status = nonfinal_smoke_test
scientific_decision = not_applicable_pilot
```

Pilot effects are nonfinal and cannot be used as Claim 1 evidence.

The dry-run graph must report:

```text
stable_task_id: global:respiratory_modifier
scope: global
manifest_row: NA
rds_id: NA
script: scripts/13_run_respiratory_modifier.R
output_schema: mitochondrial_respiratory_modifier_v1
```

## Minerva production

### Preflight

1. validate all nine Phase 07 prerequisite bundles;
2. confirm definitions are approved and frozen;
3. pass tests and the local pilot;
4. verify Git/config/lockfile parity;
5. verify memory and scratch space;
6. cap numeric-library threads at one; and
7. inspect the one-task dry-run graph and analysis fingerprint.

The validated Phase 07 bundles may use a different results root from the new
Phase 13 publication. Minerva sets
`inputs.phase13_pseudobulk_root: results/07_pseudobulk` while retaining
`outputs.root: results/minerva_production`. Phase 02, Phase 03, and Phase 04
prerequisites continue to resolve below the production stage root; only the
Phase 07 pseudobulk bundle uses the explicit input override. The local pilot
omits the override and keeps its existing stage-relative behavior.

Phase 13 reads the much smaller Phase 07 pseudobulk bundles. If Phase 07 must
first be rerun from raw RDS files, its own resource plan must process the large
source objects safely; that prerequisite is not a Phase 13 stability analysis.

If any of the nine bundles are missing, run the corresponding existing Phase 07
tasks before the
Phase 13 dry run:

```bash
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk --rds-id astrocytes

Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk --rds-id excitatory_set1

Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk --rds-id excitatory_set2

Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk --rds-id excitatory_set3

Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk --rds-id immune

Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk --rds-id inhibitory

Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk --rds-id opcs

Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk --rds-id oligodendrocytes

Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk --rds-id vasculature
```

Then require all nine matching `*.pseudobulk_status.tsv` files to report
`validated_complete`.

### Commands

```bash
cd /sc/arion/work/zhuane01/alzheimer

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

Rscript tests/test_phase13_respiratory_modifier.R

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase respiratory_modifier \
  --dry-run

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase respiratory_modifier

Rscript tests/test_phase13_respiratory_modifier.R \
  --validate-output results/minerva_production/13_respiratory_modifier \
  --expected-contexts 7 --expected-tests 196 \
  --expected-stratum-rows 168 \
  --expected-status validated_complete
```

Rerun the identical command to resume a hash-compatible incomplete run.
Checkpoint location:

```text
<execution.temp_dir>/13_respiratory_modifier/<analysis_fingerprint>/
```

Phase 13 uses `execution.phase13_stability_workers` fork workers for the
independent donor-bootstrap, leave-one-donor-out, and group-size-balanced
repetitions. The effective count is capped by `max_total_cores`, the cores
visible on the host, and the LSF/Slurm/SGE allocation when one is reported.
Minerva production requests 48 workers; the local pilot keeps one. Every job
sets its frozen identifier-derived seed, and results are restored to canonical
task order before they are combined, so changing the worker count does not
change the scientific result. BLAS/OpenMP thread counts remain one to avoid
nested oversubscription. Completed stability contexts are checkpointed
separately and reused by a hash-compatible resumed run.

The resume-compatibility fingerprint covers required input artifacts,
scientific scripts, YAML/module/manifest files, pipeline configuration, and
`renv.lock`. Test hashes and Git revision are recorded as provenance but are
not compatibility keys, so an unrelated documentation or test-only edit does
not invalidate scientific checkpoints.

Publication order is:

```text
write scientific files in staging
→ write checks
→ write artifact manifest
→ write status last inside staging
→ independently validate the complete staging bundle
→ atomically rename staging to the final directory
```

The artifact manifest hashes every declared scientific output except itself and
`respiratory_status.tsv`. The status row stores the completed artifact-manifest
SHA-256, avoiding a self-referential checksum.

The `--validate-output` mode checks exact filenames and no subdirectories,
environment-specific status, four modules, 273 memberships, seven contrasts,
28 or 196 unique test/result/stability/gate rows, 24 or 168 stratum rows, terminal
row statuses, all blocking checks, and every declared artifact hash.

## Required checks and acceptance criteria

### Blocking checks

The independent validation must confirm:

- 7 contexts, 12 groups, 7 contrasts, 4 modules, 273 memberships, and 196 tests;
- module sizes 13, 86, 155, and 19;
- `MRPL13` is present and `RPL13` is not substituted;
- nuclear OXPHOS has no mtDNA gene and excludes `ATP5IF1`, `CYCS`, and `HCCS`;
- all upstream statuses/hashes and the nine source IDs validate;
- the diagnosis/sex/APOE-by-study table is saved and study has both expected
  levels;
- excitatory barcodes do not overlap and feature order is identical;
- donor metadata and donor/context keys are unique;
- gene-wise, nucleus, and total-UMI conservation is exact;
- all genes, not module-only genes, enter filtering and TMM;
- every eligible design is full rank and includes age, PMI, and study once;
- hand-worked direct contrasts reproduce `+1,-1,-1,+1`;
- NCI references use NCI donors in the matching context only;
- module coverage, scores, and standardization independently reproduce;
- NCI-only PC1 scaling and orientation independently reproduce;
- `camera` uses the matching full tested background;
- both separate 196-test BH corrections independently reproduce;
- P/q values are within [0,1] where testable;
- whole donors, never nuclei, are bootstrapped or omitted;
- 1,000 bootstrap and 1,000 balance repetitions are present where eligible;
- at least 950 bootstrap and 950 balance repetitions succeed per eligible row;
- long-form stability rows reproduce the 196-row summaries;
- the severe-QC fraction and omission reliability rules reproduce;
- every gate Boolean reproduces from a named source field;
- no <10-donor row passes the internal confirmation gate;
- supporting modules cannot pass the broad respiratory clause;
- pilot artifacts are absent from production provenance;
- all expected artifacts have hashes and no unlisted final file exists; and
- all blocking checks pass before status publication.

### Four acceptance gates

1. **Structural:** every expected artifact and planned row exists; identifiers,
   counts, schemas, and terminal statuses validate.
2. **Scientific computation:** every eligible model and stability branch
   finishes; ineligible rows have reasons; estimates, intervals, FDR, and gate
   arithmetic reproduce.
3. **Reproducibility:** fingerprints, seeds, hashes, ordering, resume behavior,
   pilot/production separation, and atomic publication validate.
4. **Claim readiness:** each supported sentence maps to a passing row; e2 is
   provisional; supporting programs are named narrowly; causal and
   cell-type-specific wording is absent.

No positive finding is required to complete Phase 13.

## Interpretation and downstream handoff

- **If supported:** freeze the exact passing context, contrast, module,
  direction, and estimate; make the C1 figure; then run C2, C3, candidate, and
  external-replication work only as needed for later clauses.
- **If provisional:** report the large estimate, interval, donor counts, and
  instability honestly; do not headline an e2-only finding.
- **If inconclusive:** seek more donors or an independent frozen test; do not
  screen new modules until one is significant.
- **If precisely not supported:** remove the sex/APOE modifier clause. An
  overall AD program or narrower translation/membrane finding may still be
  reported if separately supported.

Network candidates cannot rescue a failed C1 result.

Figure-ready files are donor scores, stratum effects, direct module results,
`camera` results, stability summaries, and gate decisions. A later figure
workflow can show donor values, adjusted effects and intervals, direct
difference-of-differences, counts, q values, bootstrap stability, and donor
influence without changing Phase 13 inference.

## Completion criteria

Phase 13 is complete only when:

1. definitions and thresholds are approved and frozen;
2. Phase 07 production prerequisites validate;
3. implementation and synthetic tests pass;
4. the local pilot is validated and labeled nonfinal;
5. Minerva production publishes atomically;
6. all blocking checks pass;
7. all 196 rows have terminal technical and scientific statuses;
8. stability summaries reproduce;
9. claim wording follows the gate;
10. every input/output has provenance; and
11. an independent output-only validation passes.

Production completion is `validation_status = validated_complete` regardless
of the biological decision.

## Implementation checklist

### Freeze

- [ ] Approve title, boundary, contexts, contrasts, modules, and signs.
- [ ] Approve coverage, donor, SESOI, FDR, and stability rules.
- [ ] Resolve all module genes, especially `MRPL13`.
- [ ] Freeze configuration, memberships, code revision, and hashes.

### Prepare and implement

- [ ] Verify or run the nine Phase 07 production prerequisites.
- [ ] Audit source features, barcodes, donor metadata, and conservation.
- [ ] Add config, module TSV, global script, and tests.
- [ ] Register `respiratory_modifier` in the pipeline/configs.
- [ ] Implement broad counts, gene models, scores, `camera`, stability, gate,
  checkpoints, and atomic publishing.

### Validate and execute

- [ ] Pass synthetic tests and the 28-row local smoke test.
- [ ] Confirm pilot status and production separation.
- [ ] Run Minerva tests and dry run.
- [ ] Execute/resume production.
- [ ] Independently validate 196 rows, both FDR families, stability, hashes,
  and blocking checks.
- [ ] Publish status last.

### Locked result review

- [ ] Assign every row a terminal scientific status.
- [ ] Separate sex, APOE, direct-respiratory, and supporting conclusions.
- [ ] Label e2 and all low-power evidence.
- [ ] Write permitted wording and choose the next round from the gate outcome.
