# Phase 15 mitonuclear-coupling results explained

## Total number of expected results

The Phase 15 production analysis is expected to produce **168 formal endpoint
test results**:

```text
21 general endpoint tests
+ 147 sex/APOE-modifier endpoint tests
= 168 formal endpoint tests
```

This is the most important result count. The 168 rows are the tests that
receive effect estimates, confidence intervals, P values, q values, and
endpoint-level scientific statuses.

### What “context” means in this guide

In Phase 15, **context means a broad cell type, also called a broad cell
class**. The terms `context`, `cell context`, and `broad cell context` all refer
to one of these seven broad cell types:

| Context ID | Broad cell type | Analysis role |
|---|---|---|
| `astrocytes` | Astrocytes | Primary confirmatory |
| `excitatory_neurons` | Excitatory neurons | Primary confirmatory |
| `inhibitory_neurons` | Inhibitory neurons | Primary confirmatory |
| `immune_cells` | Immune cells | Secondary extension |
| `opcs` | Oligodendrocyte precursor cells | Secondary extension |
| `oligodendrocytes` | Oligodendrocytes | Secondary extension |
| `vasculature` | Vasculature cells | Secondary extension |

The statistical sample is:

```text
one donor × one broad cell type
```

For example, Phase 15 can use one astrocyte expression profile and one
excitatory-neuron expression profile from the same donor. These profiles are
kept separate because they represent different broad cell types. The donor is
still the independent person; individual nuclei are not treated as separate
people.

Each broad profile combines all eligible nuclei and fine transcriptomic
subtypes belonging to that donor and broad cell type. For example:

```text
all eligible astrocyte fine subtypes from Donor A
    → one Donor A astrocyte profile
```

In this Phase 15 guide, `context` does **not** mean:

- a fine cell subtype such as `Ast GRM3`;
- an individual nucleus;
- an AD, NCI, sex, or APOE group;
- a brain region; or
- a laboratory condition.

Therefore, “a general result in the excitatory-neuron context” means:

> The result was estimated within the donor-level broad excitatory-neuron
> profiles.

It does not mean that every fine excitatory-neuron subtype shows the same
effect. Fine-subtype localization would require a separate analysis.

Phase 15 tests the mitonuclear relationship **within** each broad cell type. It
does not directly test whether two broad cell types differ. Direct
broad-cell-type comparisons belong to Phase 14.

### Breakdown by primary and secondary broad cell types

| Result family | Calculation | Expected rows | Role |
|---|---:|---:|---|
| Primary general | 3 endpoints × 3 primary contexts | 9 | Confirmatory overall AD-related results |
| Primary modifier | 3 endpoints × 7 modifiers × 3 primary contexts | 63 | Confirmatory sex/APOE differences |
| Secondary general | 3 endpoints × 4 secondary contexts | 12 | Extension beyond the three primary contexts |
| Secondary modifier | 3 endpoints × 7 modifiers × 4 secondary contexts | 84 | Secondary sex/APOE extensions |
| **Total** | 9 + 63 + 12 + 84 | **168** | All formal endpoint tests |

The same total can also be written as:

```text
general tests:
    7 contexts × 3 endpoints = 21

modifier tests:
    7 contexts × 7 modifiers × 3 endpoints = 147

all endpoint tests:
    21 + 147 = 168
```

### The three endpoints repeated in each group

Every general context or context-by-modifier question receives three result
rows:

1. `standardized_difference`: mtDNA score minus nuclear OXPHOS score;
2. `nci_reference_residual`: observed mtDNA score minus its NCI-reference
   prediction; and
3. `coupling_slope_change`: AD-minus-NCI change in the relationship between
   the nuclear and mtDNA scores.

### Additional rows that are not additional independent tests

Phase 15 also produces explanatory rows and summary decisions:

| Output type | Calculation | Expected rows | Purpose |
|---|---:|---:|---|
| Stratum effects | 7 contexts × 6 sex/APOE strata × 3 endpoints | 126 | Show the component AD-minus-NCI effects used to build general and modifier contrasts |
| General C3 gates | 7 contexts | 7 | Combine three endpoint results into one general C3 decision per context |
| Modifier C3 gates | 7 contexts × 7 modifiers | 49 | Combine three endpoint results into one C3 decision per context and modifier |

If these three types are added to the 168 endpoint rows, the main
interpretation tables contain:

```text
168 endpoint-test rows
+ 126 descriptive stratum rows
+ 7 general gate rows
+ 49 modifier gate rows
= 350 rows
```

However, it would be incorrect to call these “350 independent tests.” The 126
stratum rows explain the contrasts, and the 56 gate rows summarize sets of
endpoint tests. The formal inferential endpoint-test count remains **168**.

## How the result values are calculated

The calculation happens in several layers. The examples below use simplified
numbers to explain the meaning. The actual model adjusts for age at death,
postmortem interval, and ROS-versus-MAP study and calculates uncertainty from
the complete fitted covariance matrix.

### Layer 1: two expression scores for each donor

For donor `d` in cell context `c`:

```text
M(d,c) = standardized mtDNA OXPHOS score
N(d,c) = standardized nuclear OXPHOS score
```

Both scores come from Phase 13 and use NCI donor distributions to define their
scales.

### Layer 2: calculate two donor-level values and one fitted relationship

D and R are calculated separately for each donor. The slope is not a separate
number assigned to one donor; it is estimated from the relationship across
donors within the required groups.

The compartment-difference endpoint is:

```text
D(d,c) = M(d,c) − N(d,c)
```

Example:

```text
M = +0.80
N = +0.20
D = +0.80 − (+0.20) = +0.60
```

The NCI-reference residual is:

```text
R_raw(d,c)
    = observed M(d,c)
      − M(d,c) predicted from the NCI relationship
```

Example:

```text
observed M             = +1.00
NCI-reference predicted M = +0.40
R_raw                  = +1.00 − (+0.40) = +0.60
```

The raw residual is then standardized using the cross-fitted NCI residual
distribution.

The slope endpoint is estimated from how M changes as N changes. For example:

```text
NCI slope = +0.90
AD slope  = +0.40

AD-minus-NCI slope change
    = +0.40 − (+0.90)
    = −0.50
```

### Layer 3: calculate an AD effect within each sex/APOE stratum

For endpoint `Y`, where Y can be D, R, or the slope, define:

```text
DeltaY(sex, APOE, context)
    = adjusted AD value
      − adjusted NCI value
```

For D and R, the values are adjusted group means. For the slope endpoint, the
values are fitted mtDNA-versus-nuclear slopes.

Example for D in female e4 excitatory neurons:

```text
adjusted mean D in AD  = −0.40
adjusted mean D in NCI = +0.10

DeltaD(Female,e4,excitatory)
    = −0.40 − (+0.10)
    = −0.50
```

Interpretation: AD is associated with a 0.50-unit more negative mtDNA-minus-
nuclear balance in female e4 excitatory-neuron profiles.

### Layer 4A: calculate one general endpoint result

For one context and endpoint, the general result is the equal-weight average
of the six stratum AD effects:

```text
general effect
    = [Delta(Female,e2)
       + Delta(Female,e33)
       + Delta(Female,e4)
       + Delta(Male,e2)
       + Delta(Male,e33)
       + Delta(Male,e4)] / 6
```

Suppose the six adjusted stratum effects are:

```text
Female e2  = +0.60
Female e33 = +0.40
Female e4  = +0.20
Male e2    = +0.50
Male e33   = +0.30
Male e4    = −0.20
```

Then the general estimate is:

```text
(+0.60 + 0.40 + 0.20 + 0.50 + 0.30 − 0.20) / 6
    = +1.80 / 6
    = +0.30
```

Interpretation: after giving the six sex/APOE strata equal weight, AD is
associated with a `+0.30` change in that endpoint in this context.

The arithmetic explains the target value. The actual standard error and
confidence interval use the full covariance from one fitted model; Phase 15
does not incorrectly treat six separately estimated effects as independent.

### Layer 4B: calculate one modifier endpoint result

A modifier result compares two stratum AD effects directly.

For female e4 versus female e33:

```text
modifier effect
    = DeltaY(Female,e4)
      − DeltaY(Female,e33)
```

Using two values from the example above:

```text
DeltaY(Female,e4)  = +0.20
DeltaY(Female,e33) = +0.40

modifier
    = +0.20 − (+0.40)
    = −0.20
```

Interpretation: the AD-related endpoint change is 0.20 units more negative,
or less positive, in female e4 than in female e33.

For a sex contrast within e2:

```text
DeltaY(Female,e2) = +0.60
DeltaY(Male,e2)   = +0.50

female-minus-male e2 modifier
    = +0.60 − (+0.50)
    = +0.10
```

The same formulas apply to the slope endpoint, but each `DeltaY` is then an
AD-minus-NCI **slope change** rather than a difference in group means.

### Units of the three estimates

| Endpoint | Unit of its result estimate |
|---|---|
| Difference D | Difference between an mtDNA NCI-SD score and a nuclear OXPHOS NCI-SD score |
| Residual R | Cross-fitted NCI residual standard deviations |
| Slope change | mtDNA NCI-SD units per one nuclear OXPHOS NCI-SD unit |

Every formal endpoint row also contains:

- a robust standard error;
- a 95% confidence interval;
- a P value;
- a q value corrected within its complete prespecified family;
- donor and reference counts;
- stability and sensitivity results; and
- an endpoint status.

The estimate should never be interpreted without those accompanying fields.

## How to interpret the 147 modifier result values

This section is the quickest reference for the 63 primary-modifier and 84
secondary-modifier rows. Later sections explain each endpoint and the C3 gate
in greater detail.

### The 147 rows represent 49 biological questions

Each broad-cell-type-by-modifier question receives three endpoint rows:

```text
Primary modifier questions:
    3 primary broad cell types × 7 modifiers
    = 21 questions

    21 questions × 3 endpoints
    = 63 result rows

Secondary modifier questions:
    4 secondary broad cell types × 7 modifiers
    = 28 questions

    28 questions × 3 endpoints
    = 84 result rows

All modifier questions:
    21 + 28 = 49 questions

All modifier endpoint rows:
    49 × 3 = 147 rows
```

For example, this is one modifier question:

> In broad excitatory-neuron profiles, does the AD-related mitonuclear
> expression relationship differ between female e4 and female e33 donors?

That one question receives three values:

1. a compartment-difference modifier;
2. an NCI-reference-residual modifier; and
3. a coupling-slope modifier.

The three endpoint rows are combined later into one modifier C3 gate. They
must not be counted as three independent replications.

### General formula for every modifier estimate

Let `Y` be one endpoint: D, R, or the fitted slope. Within one broad cell type,
first estimate the AD effect in each sex/APOE stratum:

```text
DeltaY(group)
    = adjusted Y in AD
      − adjusted Y in NCI
```

Then compare two stratum AD effects directly:

```text
modifier estimate
    = DeltaY(first named group)
      − DeltaY(second named group)
```

This is a difference-of-differences.

| Estimate sign | General meaning |
|---|---|
| Positive | The AD-related endpoint change is more positive, or less negative, in the first named group |
| Negative | The AD-related endpoint change is more negative, or less positive, in the first named group |
| Near zero | The AD-related endpoint change is similar between the two groups |

The sign cannot be interpreted until the first and second groups in the
`contrast_id` are known.

### The seven frozen modifier subtraction orders

| `contrast_id` | First group | Second group | Positive estimate means |
|---|---|---|---|
| `sex_F_minus_M__e2` | Female e2 | Male e2 | AD endpoint change is more positive in female e2 |
| `sex_F_minus_M__e33` | Female e33 | Male e33 | AD endpoint change is more positive in female e33 |
| `sex_F_minus_M__e4` | Female e4 | Male e4 | AD endpoint change is more positive in female e4 |
| `apoe_e2_minus_e33__Female` | Female e2 | Female e33 | AD endpoint change is more positive in female e2 |
| `apoe_e2_minus_e33__Male` | Male e2 | Male e33 | AD endpoint change is more positive in male e2 |
| `apoe_e4_minus_e33__Female` | Female e4 | Female e33 | AD endpoint change is more positive in female e4 |
| `apoe_e4_minus_e33__Male` | Male e4 | Male e33 | AD endpoint change is more positive in male e4 |

### Interpreting the compartment-difference modifier

For every donor:

```text
D = mtDNA score − nuclear OXPHOS score
```

The modifier value is:

```text
[AD − NCI change in D for group 1]
    −
[AD − NCI change in D for group 2]
```

Example in broad excitatory-neuron profiles:

```text
comparison:
    Female e4 − Female e33

DeltaD(Female,e4)  = −0.60
DeltaD(Female,e33) = −0.10

D modifier
    = −0.60 − (−0.10)
    = −0.50
```

Interpretation:

> In broad excitatory-neuron profiles, the AD-related mtDNA-minus-nuclear
> expression balance is 0.50 units more negative in female e4 than in female
> e33.

This value does not reveal which compartment produced the difference. The
separate mtDNA and nuclear score changes must be examined. A negative D
modifier could reflect relatively lower mtDNA expression, relatively higher
nuclear OXPHOS expression, or a combination.

### Interpreting the NCI-reference-residual modifier

For every donor:

```text
R = observed mtDNA score
    − mtDNA score predicted from the NCI reference relationship
```

The modifier value is:

```text
[AD − NCI change in R for group 1]
    −
[AD − NCI change in R for group 2]
```

Example:

```text
comparison:
    Female e4 − Female e33

DeltaR(Female,e4)  = −0.50
DeltaR(Female,e33) = +0.05

residual modifier
    = −0.50 − (+0.05)
    = −0.55
```

Interpretation:

> Given nuclear OXPHOS expression, the AD-related departure below the
> NCI-predicted mtDNA level is 0.55 residual standard deviations more negative
> in female e4 than in female e33.

The residual unit is one cross-fitted NCI residual standard deviation.

### Interpreting the coupling-slope modifier

The slope describes how much the mtDNA score changes when the nuclear OXPHOS
score increases by one NCI-standardized unit.

Within one stratum:

```text
slope AD effect
    = fitted slope in AD
      − fitted slope in NCI
```

The modifier value is:

```text
[slope AD effect in group 1]
    −
[slope AD effect in group 2]
```

Example for female versus male within e4:

```text
Female e4:
    NCI slope = +0.80
    AD slope  = +0.30

    female slope AD effect
        = +0.30 − (+0.80)
        = −0.50

Male e4:
    NCI slope = +0.60
    AD slope  = +0.70

    male slope AD effect
        = +0.70 − (+0.60)
        = +0.10

female-minus-male slope modifier
    = −0.50 − (+0.10)
    = −0.60
```

Interpretation:

> The AD-related change in the mtDNA-versus-nuclear OXPHOS slope is 0.60 slope
> units more negative in female e4 than in male e4.

In this example, the slope becomes weaker in female e4 AD and slightly
stronger in male e4 AD.

A slope modifier does not state whether mtDNA expression is generally higher
or lower. It describes how the relationship between M and N changes. The
prediction grid and shared nuclear-score range must also be inspected.

### Interpret the three values as one triplet

Consider one fictional primary modifier question:

```text
broad cell type:
    excitatory neurons

comparison:
    Female e4 − Female e33
```

Suppose its endpoint rows are:

| Endpoint | Modifier estimate | Endpoint status |
|---|---:|---|
| Difference D | −0.50 | `supported` |
| Residual R | −0.55 | `supported` |
| Slope change | −0.05 | `not_supported_precise_null` in this illustration |

If all compatibility and stability requirements pass, the modifier gate is:

```text
relative_imbalance
```

Allowed interpretation:

> In broad excitatory-neuron profiles, the AD-related relative balance between
> mtDNA respiratory and nuclear OXPHOS expression is more negative in female
> e4 than in female e33.

Because the slope did not pass, this triplet does not support wording about a
coupling-slope change or decoupling.

Other possible triplets are:

| Passing compatible endpoints | Gate classification |
|---|---|
| Difference + residual | `relative_imbalance` |
| Slope + one compatible level endpoint | `slope_change` |
| Difference + residual + slope | `imbalance_and_slope_change` |
| Only one endpoint, or incompatible endpoints | `partial_evidence` or `inconclusive` |

At least two compatible endpoints must carry the modifier C3 gate, and at
least one must be the residual or slope.

### Primary and secondary modifier values use the same calculation

The formula, sign, units, endpoint rules, and donor-level interpretation are
identical in primary and secondary broad cell types. Their inferential roles
differ.

| Modifier tier | Broad cell types | Testing family | What it can do |
|---|---|---:|---|
| Primary | Astrocytes, excitatory neurons, inhibitory neurons | 63 rows corrected together | Can contribute to the overall primary C3 conclusion |
| Secondary | Immune cells, OPCs, oligodendrocytes, vasculature | 84 rows corrected together | Provides a prespecified extension but cannot rescue failed primary C3 |

A supported secondary OPC result, for example, should be reported as a
secondary extension. Its mathematical meaning is not weaker, but its planned
role in the overall claim is secondary.

Phase 15 does not directly compare two broad cell types. A supported modifier
in astrocytes and an unsupported modifier in OPCs does not prove that the
contexts differ; that would require a Phase 14-style direct context comparison.

### Read these fields with every modifier estimate

| Field | Why it matters |
|---|---|
| `context_id` | Identifies the broad cell type |
| `contrast_id` | Defines the first and second sex/APOE groups |
| `endpoint_id` | Identifies D, residual, or slope and therefore the units |
| Estimate | Gives the direction and size of the difference-of-differences |
| 95% confidence interval | Shows precision and whether zero remains plausible |
| q value | Shows evidence after correcting the full 63- or 84-row family |
| Four donor counts | Determines whether the modifier can be confirmatory, provisional, or untestable |
| NCI reference count | Determines whether a residual result can be confirmatory |
| Predictor-range overlap | Determines whether a slope comparison is supported by overlapping data |
| Stability results | Show whether donor resampling, donor removal, alternative scores, normalization, and QC preserve the result |
| Endpoint status | States whether one endpoint passed |
| Three-endpoint gate | States whether the modifier-specific C3 claim passed |

Each endpoint uses a prespecified absolute meaningful-effect threshold of
`0.25` in its own units. A supported endpoint generally requires:

```text
q <= 0.05
absolute estimate >= 0.25
95% confidence interval excludes zero
confirmation donor/reference counts pass
all mandatory stability checks pass
```

A large estimate with a wide interval is not automatically supported.

The main modifier question is:

> Within this broad cell type and for this endpoint, how much more positive or
> negative is the AD-versus-NCI endpoint change in the first named sex/APOE
> group compared with the second named group?

The complete C3 conclusion comes from the compatible three-endpoint triplet,
not from one modifier value viewed alone.

## Current result status

As of 2026-08-09, Phase 15 has not produced real biological ROSMAP results in
the shared workspace. This production directory is absent:

```text
results/minerva_production/15_mitonuclear_coupling/
```

The [formal Phase 15 plan](phase_15_mitonuclear_coupling_plan.md) records a
successful synthetic pilot. That pilot tests the code, formulas, schemas,
cross-fitting, and decision rules. Synthetic results are deliberately created
examples and cannot provide evidence about Alzheimer disease.

The examples in this guide are therefore illustrations of how future Phase 15
production results should be interpreted. They are not observed ROSMAP
findings.

The companion
[definition and stratification guide](phase_15_definition_data_and_stratification.md)
provides additional background.

## 1. What Phase 15 studies

Phase 15 compares two donor-level expression scores:

```text
M = mtDNA-encoded OXPHOS score
N = nuclear-encoded structural OXPHOS score
```

The two gene sets represent different genetic compartments:

- the mtDNA score uses 13 respiratory genes encoded by mitochondrial DNA;
- the nuclear score uses 86 respiratory-complex structural genes encoded by
  nuclear DNA.

These compartments must cooperate to build the respiratory-chain machinery.

The central Phase 15 question is:

> Does AD alter the RNA-expression relationship between mtDNA respiratory
> genes and nuclear OXPHOS genes?

Phase 15 examines this relationship separately in each broad cell context. It
does not directly compare the contexts with one another. A result supported in
astrocytes but unsupported in neurons does not prove the contexts differ.
Direct context comparison belongs to Phase 14.

## 2. Why Phase 15 uses three endpoints

One formula might make a result look stronger or weaker simply because of how
the relationship was summarized. Phase 15 therefore examines the same broad
biological relationship in three planned ways:

1. the difference between mtDNA and nuclear scores;
2. departure from the relationship learned in NCI donors; and
3. change in the slope connecting nuclear and mtDNA scores.

A strong C3 conclusion generally requires at least two compatible endpoints.
At least one of those endpoints must be the NCI-reference residual or the
coupling slope.

## 3. Endpoint 1: compartment difference

For every donor and cell context, calculate:

```text
D = M − N
```

### Donor-level example

Suppose one donor has:

```text
mtDNA score M          = +0.80
nuclear OXPHOS score N = +0.20

D = +0.80 − (+0.20) = +0.60
```

This donor's mtDNA expression is relatively higher than their nuclear OXPHOS
expression on the two NCI-standardized score scales.

### Interpreting an individual donor's D

| D value | Meaning |
|---|---|
| Positive | mtDNA expression is relatively higher than nuclear OXPHOS expression |
| Negative | mtDNA expression is relatively lower than nuclear OXPHOS expression |
| Near zero | The two NCI-standardized scores are similar |

### What the result row tests

The Phase 15 result is not usually the individual donor's D. It tests whether
D changes between AD and NCI:

```text
AD effect on D
    = model-adjusted mean D in AD
      − model-adjusted mean D in NCI
```

### Illustrative result

```text
AD effect on D = +0.50
95% CI = [+0.20, +0.80]
q = 0.01
```

Plain-language interpretation:

> In this cell context, AD is associated with a shift of 0.50 score units
> toward relatively higher mtDNA expression compared with nuclear OXPHOS
> expression.

This does not identify which compartment produced the difference. Possible
explanations include:

- mtDNA expression increased;
- nuclear OXPHOS expression decreased; or
- both changed in different directions or by different amounts.

The separate M and N results must be examined to identify the components.

D measures relative level balance. It does not by itself prove that the slope
connecting M and N changed.

## 4. Endpoint 2: NCI-reference residual

This endpoint asks:

> Given a donor's nuclear OXPHOS score, what mtDNA score would be predicted
> from the relationship estimated in NCI donors?

NCI means the comparison group labeled no cognitive impairment. It does not
mean pathology-free or biologically normal.

Within each cell context, Phase 15 builds an NCI-only reference model:

```text
predicted M = function of N and the planned covariates
```

It then calculates:

```text
raw residual
    = observed mtDNA score
      − mtDNA score predicted from the NCI reference
```

### Donor-level example

Suppose a donor has:

```text
nuclear OXPHOS score          = +0.50
NCI model predicts mtDNA score = +0.40
observed mtDNA score           = +1.00

raw residual = +1.00 − (+0.40) = +0.60
```

The donor's mtDNA score is higher than expected from the NCI reference
relationship.

### Interpreting a residual

| Residual | Meaning |
|---|---|
| Positive | mtDNA expression is higher than predicted from the NCI relationship |
| Negative | mtDNA expression is lower than predicted |
| Near zero | mtDNA expression follows the NCI reference prediction |

The residual is standardized using the cross-fitted NCI residual distribution.
One standardized residual unit is one NCI residual standard deviation in that
cell context.

### Why cross-fitting is used

An NCI donor must not help train the exact model that predicts that same donor.
Phase 15 divides NCI donors into training and held-out folds:

1. fit the relationship using four folds;
2. predict the NCI donors in the held-out fold;
3. repeat until every NCI donor has a prediction from a model that did not
   contain them; and
4. predict AD donors using only NCI-trained models.

This prevents the reference model from looking artificially accurate because
it has already seen the donor being evaluated.

### Illustrative result

```text
AD effect on standardized residual = +0.45
95% CI = [+0.15, +0.75]
q = 0.02
```

Interpretation:

> In this cell context, AD donors have mtDNA expression that is approximately
> 0.45 NCI residual standard deviations higher than predicted from the NCI
> mtDNA-nuclear relationship.

### Candidate-bridge rule

The residual is the planned shared endpoint for later candidate-system work.
It can be used as that bridge only if:

1. the residual endpoint itself is supported;
2. the full matching C3 gate passes;
3. its reference and cross-fold stability checks pass; and
4. the full frozen 13-versus-86 gene relationship is retained.

Calculating a residual does not automatically authorize it as a candidate
bridge.

## 5. Endpoint 3: coupling-slope change

The slope describes how M and N move together:

```text
slope
    = change in mtDNA score
      for a one-unit increase in nuclear OXPHOS score
```

### Example

Suppose:

```text
NCI slope = +0.90
AD slope  = +0.40

slope change = +0.40 − (+0.90) = −0.50
```

Interpretation:

> The mtDNA score rises less strongly with nuclear OXPHOS expression in AD
> than in NCI.

### Interpreting the slope-change sign

- a positive slope change means the relationship became more positive or less
  negative in AD;
- a negative slope change means the relationship became less positive or more
  negative in AD.

The slope result is measured as mtDNA NCI-standard-deviation units per nuclear
OXPHOS NCI-standard-deviation unit.

### Why slope is different from D and the residual

D and the residual mainly detect relative level imbalance. The slope directly
tests whether the shape of the M-versus-N relationship changed.

Therefore, a supported slope is required for wording about an altered
coupling slope. Phase 15 does not compare:

```text
significant correlation in AD
versus
nonsignificant correlation in NCI
```

It directly tests:

```text
AD slope − NCI slope
```

### Crossing relationships

Sometimes the fitted AD and NCI lines cross. AD may be higher at low N but
lower at high N. Such a result has no single direction across the relevant
range.

The current plan labels a stable crossing result:

```text
slope_rewiring_observed
```

It is scientifically interesting but cannot make the main C3 gate pass in
this analysis version. Its crossing point and prediction range should be
reported separately.

## 6. General versus modifier-specific results

Phase 15 produces two kinds of scientific results.

### General C3 result

The general result asks:

> On average across the six sex-by-APOE strata, does AD alter this endpoint?

The six strata are:

```text
Female e2
Female e33
Female e4
Male e2
Male e33
Male e4
```

Each stratum receives equal weight, so the largest donor group does not
dominate the conclusion.

Phase 15 produces:

```text
7 contexts × 3 endpoints = 21 general endpoint rows
```

The three primary confirmatory contexts are:

- astrocytes;
- excitatory neurons; and
- inhibitory neurons.

Immune cells, OPCs, oligodendrocytes, and vasculature are secondary
extensions. Secondary results are reported but cannot rescue a failed primary
C3 conclusion.

### Modifier-specific C3 result

The modifier result asks:

> Does the AD-related mtDNA-nuclear relationship differ by recorded sex or
> APOE group?

For example:

```text
AD effect on D in female e4
    −
AD effect on D in female e33
```

There are seven inherited sex/APOE contrasts:

```text
7 contexts × 7 modifiers × 3 endpoints = 147 modifier endpoint rows
```

A modifier result can pass even if the general result does not. Opposite
subgroup effects can cancel when the six strata are averaged.

### Descriptive stratum effects

Phase 15 also saves:

```text
7 contexts × 6 strata × 3 endpoints = 126 descriptive stratum rows
```

These explain the general and modifier contrasts. They are not another family
of primary C3 hypotheses.

## 7. Worked example: relative imbalance without a slope change

Suppose excitatory neurons produce these fictional results:

| Endpoint | Estimate | Status |
|---|---:|---|
| Difference D | +0.50 | Supported |
| Residual R | +0.45 | Supported |
| Slope change | +0.05 | Not supported |

If all compatibility and stability requirements pass, the C3 classification
is:

```text
relative_imbalance
```

Allowed interpretation:

> In ROSMAP excitatory-neuron profiles, AD was associated with altered
> relative balance between mtDNA-encoded respiratory and nuclear-encoded
> OXPHOS expression.

Do not call this “decoupling,” because the slope did not change.

## 8. Worked example: slope change

Suppose astrocytes produce these fictional results:

| Endpoint | Estimate | Status |
|---|---:|---|
| Difference D | −0.35 | Supported |
| Residual R | −0.10 | Not supported |
| Slope change | −0.45 | Supported |

If D and the slope predictions are biologically compatible throughout the
shared nuclear-score range, the classification is:

```text
slope_change
```

Possible interpretation:

> In astrocytes, AD was associated with a more negative relative expression
> balance and a weaker mtDNA-versus-nuclear OXPHOS expression slope.

The exact direction must be described using the fitted prediction grid, not
the slope number alone.

## 9. Worked example: sex/APOE modification

Suppose the endpoint is D in excitatory neurons:

```text
AD effect on D in female e4  = −0.60
AD effect on D in female e33 = −0.10
```

The direct modifier is:

```text
female e4 − female e33
    = −0.60 − (−0.10)
    = −0.50
```

Interpretation:

> The AD-associated mtDNA-versus-nuclear relative balance is 0.50
> standardized units more negative in female e4 donors than in female e33
> donors.

If the residual gives a compatible supported result, this pair could produce
modifier-specific `relative_imbalance`.

This does not mean that the same modifier occurs in every cell context.

## 10. Worked example: endpoints disagree

Suppose:

```text
difference estimate = +0.50
residual estimate   = −0.45
```

Even if both have small q values, they point in opposite biological
directions. They cannot be combined into a passing C3 conclusion.

Depending on the slope and remaining evidence, the gate would generally be:

```text
partial_evidence
```

or `inconclusive`.

This prevents two statistically detectable but biologically contradictory
results from being combined into a misleading conclusion.

## 11. How the C3 gate works

A context-level C3 claim requires:

1. At least two of the three endpoints pass.
2. At least one passing endpoint is the residual or slope.
3. The carrier endpoints have compatible biological directions.
4. Their confidence intervals, q values, and meaningful-effect thresholds
   pass.
5. Donor-count and reference-model requirements pass.
6. Bootstrap and leave-one-donor-out checks pass.
7. PC1, normalization, 50-nucleus, QC, reference, and gene/complex omission
   checks agree.

### Supported C3 classifications

| Classification | Passing pattern | Meaning |
|---|---|---|
| `relative_imbalance` | Difference + residual | Relative expression balance changed |
| `slope_change` | Slope + one compatible level endpoint | Coupling slope changed |
| `imbalance_and_slope_change` | All three | Both level balance and slope changed |

The difference and residual are related transformations of the same M and N
scores. They are corroborating views, not independent replication.

It is possible for C3 to pass using the difference and slope while the
residual does not pass. In that case, C3 slope wording may be permitted, but
the residual cannot be authorized as the later candidate bridge.

## 12. How to read the endpoint statuses

Every general and modifier endpoint row receives one status.

| Status | Meaning |
|---|---|
| `supported` | Effect, q value, confidence interval, donor eligibility, and every mandatory stability rule passed |
| `provisional_low_power` | Other rules passed, but donor or NCI-reference counts were too small |
| `statistically_detectable_but_small` | Statistically detectable, but smaller than the planned 0.25 threshold |
| `not_supported_precise_null` | The complete confidence interval lies inside −0.25 to +0.25 |
| `inconclusive` | The estimate is too uncertain, unstable, or incomplete |
| `not_testable` | Required data, variance, model rank, or reference fitting were insufficient |

The `0.25` threshold is a project decision defined before opening results. It
is not a universal biological law.

A q value above `0.05` is not automatically evidence of no effect. A wide
confidence interval usually means the result is inconclusive.

## 13. How to read the gate statuses

Phase 15 combines the three endpoints into:

- seven general context gates; and
- 49 modifier context-by-contrast gates.

Each gate receives one of these statuses:

| Gate status | Meaning |
|---|---|
| `supported` | At least two compatible required endpoints and every gate rule passed |
| `provisional_low_power` | The scientific pattern passed, but confirmation counts did not |
| `partial_evidence` | One endpoint passed, two endpoints disagreed, or two valid compatible carriers were unavailable |
| `not_supported_precise_null` | All three estimable endpoint intervals lie inside their small-effect ranges and none passes |
| `inconclusive` | The available intervals or stability evidence cannot decide |
| `not_testable` | Too little valid information exists to apply the gate |

## 14. Overall Phase 15 conclusion

Only the three primary contexts determine the overall primary C3 label.

| Overall result | Meaning |
|---|---|
| `supported_general_and_modifier` | At least one primary context has general C3 support and at least one has modifier-specific support |
| `supported_general_only` | General C3 is supported, but no modifier contrast is supported |
| `supported_modifier_only` | A modifier-specific result is supported, but no general result is supported |
| `provisional` | No primary gate is supported, but at least one is provisionally supported |
| `not_supported` | Adequately precise primary results rule out the planned meaningful effects |
| `inconclusive` | Wide intervals, instability, mixed results, or incomplete evidence prevent a conclusion |
| `not_testable` | Primary C3 could not be evaluated |

Secondary-context support is reported as secondary evidence and cannot turn a
failed or inconclusive primary result into overall support.

## 15. Which result files should be read?

Once Minerva production runs and validates, use these files in order:

1. `mitonuclear_status.tsv` — technical and top-level scientific state.
2. `mitonuclear_claim_summary.tsv` — overall general, modifier, secondary, and
   bridge conclusions.
3. `mitonuclear_general_gate_decisions.tsv` — one general C3 decision per
   context.
4. `mitonuclear_modifier_gate_decisions.tsv` — one decision per context and
   modifier.
5. `mitonuclear_general_results.tsv` — the 21 general endpoint estimates.
6. `mitonuclear_modifier_results.tsv` — the 147 modifier endpoint estimates.
7. `mitonuclear_general_stability_summary.tsv` and
   `mitonuclear_modifier_stability_summary.tsv` — robustness evidence.
8. `mitonuclear_donor_endpoints.tsv.gz` — donor-level D and residual values.
9. `mitonuclear_group_slopes.tsv` and
   `mitonuclear_prediction_grid.tsv.gz` — slope interpretation.
10. `mitonuclear_qc_normalization_sensitivity.tsv` and
    `mitonuclear_gene_complex_influence.tsv` — technical and biological
    sensitivity evidence.

The gate-decision tables control final wording. A visually large estimate
cannot override a failed gate.

## 16. A simple reading order for one future result

For a general or modifier endpoint row:

1. **Identify the context.** Is it one of the three primary contexts or a
   secondary extension?
2. **Identify the scope.** Is it a general AD result or a sex/APOE modifier?
3. **Identify the endpoint.** Difference, residual, or slope?
4. **Read the sign and magnitude.** Interpret them using the endpoint's
   definition and contrast order.
5. **Read the 95% confidence interval.** Does it exclude zero, and how wide is
   it?
6. **Read the q value.** Did the row survive its complete prespecified testing
   family?
7. **Check donor and reference counts.** Is it confirmatory, provisional, or
   untestable?
8. **Check stability.** Bootstrap, leave-one-donor-out, PC1, normalization,
   50-nucleus, QC, reference, and omission analyses must agree.
9. **Read the endpoint status.** Do not assign a label visually.
10. **Read the matching three-endpoint gate.** One endpoint cannot establish
    C3 alone.
11. **Check the classification.** Relative imbalance, slope change, both, or
    partial/inconclusive evidence?
12. **Check bridge authorization.** A supported residual is not automatically
    an authorized bridge.

## 17. What Phase 15 cannot prove

Even a supported Phase 15 result demonstrates an RNA-expression relationship
in the ROSMAP donors. It does not prove:

- mitochondrial respiration changed;
- ATP production changed;
- mtDNA copy number changed;
- one gene caused the relationship;
- a result is specific to one cell context;
- the result independently replicated; or
- a candidate gene regulates the relationship.

The strongest safe computational wording is an internally supported
AD-associated change in the mtDNA-versus-nuclear OXPHOS RNA-expression
relationship, named for the exact cell context and, when applicable, the exact
sex/APOE comparison.
