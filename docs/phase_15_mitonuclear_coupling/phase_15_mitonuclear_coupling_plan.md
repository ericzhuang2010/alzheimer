# Phase 15: Donor-Level Test of AD-Associated Mitonuclear Expression Coupling

## Status and phase boundary

This document defines the scientific, implementation, execution, output, and
completion plan for Phase 15.

Plan status: **draft for review; not approved for execution**.

Phase 15 tests **Claim 3 (C3), Mitonuclear coupling**:

> Does Alzheimer disease alter the RNA-expression relationship between
> mitochondrial-DNA respiratory genes and nuclear-DNA OXPHOS structural genes,
> and does that alteration differ by sex or APOE group?

Phase 15 requires a complete, independently validated Phase 13 production
bundle. It must not run on partial, pilot, or manually copied Phase 13 outputs.
The context tiers, three endpoints, reference model, direct contrasts,
effect-size thresholds, multiple-testing families, stability rules, and C3
gates must be approved before anyone opens the Phase 15 effect estimates.

Creating this plan does not run Phase 15 and does not change results from any
earlier phase.

### Short names

- Claim 1: **Respiratory modifier**
- Claim 2: **Modifier heterogeneity**
- Claim 3: **Mitonuclear coupling**

### Output roots

```text
results/local_pilot/15_mitonuclear_coupling/
results/minerva_production/15_mitonuclear_coupling/
```

Pilot files are nonfinal. They must never be copied into, combined with, or
promoted in place to the production directory.

### Companion explanation

The beginner-level definition of C3 is in:

[C3 definition, data, and stratification](phase_15_definition_data_and_stratification.md)

This implementation plan is authoritative when the companion explanation and
this plan differ. In particular, this plan explicitly separates a general AD
test from sex/APOE modifier tests and analyzes the four non-neural Phase 13
contexts as a secondary family.

## What Phase 15 will and will not do

### Phase 15 will

1. inherit the frozen 13-gene mtDNA OXPHOS score and 86-gene nuclear OXPHOS
   score from Phase 13;
2. preserve donors, not nuclei, as the independent biological samples;
3. calculate three prespecified measurements of the relationship between the
   two scores;
4. test an equal-stratum-weighted general AD-versus-NCI change in that
   relationship;
5. separately test seven direct sex/APOE differences in the AD-related change;
6. use astrocytes, excitatory neurons, and inhibitory neurons as the
   confirmatory context family;
7. analyze immune cells, OPCs, oligodendrocytes, and vasculature in a separate
   secondary family;
8. rebuild learned score and reference quantities inside donor resampling;
9. apply prespecified FDR, effect-size, eligibility, stability, and quality
   rules; and
10. publish every positive, negative, provisional, inconclusive, and
    untestable row with complete provenance.

### Phase 15 will not

- treat individual nuclei as independent observations;
- call separate mtDNA or nuclear OXPHOS differential expression a mitonuclear
  relationship change;
- choose whichever of the three endpoints has the smallest P value;
- choose contexts, contrasts, score definitions, or quality rules after seeing
  Phase 15 effects;
- test all 54 fine cell types;
- test whether the C3 effect differs statistically between cell contexts;
- use Phase 14 results as an input or selection rule;
- test `APOE–TUFM`, `LAMTOR5–ATP5IF1`, or
  `GABARAPL2–CHCHD2/PARK7`;
- use Phase 12 KDA or any network result;
- infer oxygen consumption, ATP production, mitochondrial mass, mtDNA copy
  number, organelle function, or causal regulation from RNA expression;
- call an effect cell-type-specific merely because it passes in one context;
  or
- render final publication figures.

Phase 15 creates validated, figure-ready data. Candidate bridges, network
validation, external replication, functional assays, and final figures belong
to later phases.

## The scientific question in plain language

### Why two genomes are involved

The respiratory chain is built from proteins encoded in two places:

- mitochondrial DNA, called **mtDNA**, encodes 13 respiratory-chain proteins;
- nuclear DNA encodes most of the other structural OXPHOS proteins.

The two sets normally need to be coordinated. Phase 15 asks whether their
RNA-expression relationship is different in AD.

This is not the same as asking whether one set is higher or lower by itself.
For example:

```text
nuclear OXPHOS decreases by 0.5 units
mtDNA OXPHOS also decreases by 0.5 units
```

The two compartments changed, but their balance may have stayed similar.

In contrast:

```text
nuclear OXPHOS decreases by 0.2 units
mtDNA OXPHOS decreases by 1.0 unit
```

The mtDNA signal moved much farther. That may indicate an altered relationship
and motivates the formal C3 tests.

### A residual example

Suppose the NCI reference predicts an mtDNA score of `0.7` for a donor with a
particular nuclear OXPHOS score. The observed mtDNA score is `0.2`:

```text
residual = observed mtDNA - predicted mtDNA
         = 0.2 - 0.7
         = -0.5
```

The negative residual means that this donor's mtDNA expression is lower than
expected from the relationship estimated in the NCI comparison group.

“NCI reference” does not mean biologically normal or pathology-free. It means
only that the expected relationship was estimated from donors labeled NCI.

### Why three measurements are required

No single number completely describes the relationship. Phase 15 therefore
uses three measurements:

1. **standardized difference:** is the mtDNA score relatively higher or lower
   than the nuclear score?
2. **NCI-reference residual:** is mtDNA expression above or below the value
   predicted from the NCI relationship?
3. **coupling-slope change:** does the strength of the mtDNA-versus-nuclear
   relationship change?

At least two measurements must support the claim. One must be the residual or
the slope. This prevents a simple difference score from carrying the full C3
claim by itself.

## Relationship to Phases 13 and 14

### What Phase 15 inherits from Phase 13

Phase 13 builds one all-gene profile per donor and broad cell context, freezes
the two respiratory gene sets, normalizes expression, and calculates the two
donor scores.

Phase 15 does not redefine those gene sets. It pairs the two Phase 13 scores
for the same donor and context, then performs new relationship tests.

```text
Phase 13:
    Does sex or APOE modify the AD effect on either respiratory score?

Phase 15 general C3:
    Does AD alter the relationship between the two scores?

Phase 15 modifier C3:
    Does that AD-related relationship change differ by sex or APOE?
```

The Phase 13 plan is:

[Phase 13 respiratory modifier plan](../phase_13_repiratory_modifier/phase_13_respiratory_modifier_plan.md)

Phase 15 must run for every eligible frozen context regardless of whether the
matching Phase 13 C1 row was positive. Selecting only positive Phase 13 rows
would bias the C3 test.

A technically validated Phase 13 bundle is required. A scientifically positive
C1 result is not required for running Phase 15.

### Why Phase 14 is not a dependency

Phase 14 tests whether a Phase 13 module modifier differs between broad cell
contexts. It does not test whether a mitonuclear endpoint differs between
contexts.

Therefore:

- Phase 15 depends directly on Phase 13;
- Phase 14 is neither an input nor a blocker; and
- a future direct between-context analysis would be required before describing
  C3 as cell-context-specific.

### Discovery evidence is motivation, not an input

Phase 08 DEGs, Phase 10 similarity scores, Phase 11 pathway results, and Phase
12 KDA results motivated C3. The Phase 15 scientific script must not read them.

## Plain-language map of the workflow

```text
Validate the Phase 13 production bundle
                  |
                  v
Pair mtDNA and nuclear OXPHOS scores for each donor/context
                  |
                  v
Build the three fixed C3 measurements
     |                 |                    |
     v                 v                    v
 difference        NCI residual        slope change
     \                 |                    /
      \                |                   /
       +---- general AD and modifier tests +
                          |
                          v
       correct all planned tests in frozen families
                          |
                          v
       bootstrap, leave-one-donor-out, score, QC,
       reference-model, normalization, and influence checks
                          |
                          v
          apply the locked C3 gate and publish
```

## Frozen scientific design

### Unit of analysis

The independent biological sample is:

```text
one donor × one broad cell context
```

The same donor may contribute several contexts. Phase 15 fits each context
separately, but donor bootstrap and leave-one-donor-out analyses must keep all
of a donor's contexts together. Nuclei are never resampled as if they were
people.

### Seven broad cell contexts in two tiers

The existing C3 definition freezes three neural contexts as confirmatory. The
expanded Phase 13 bundle also contains four additional broad contexts. Phase
15 analyzes all seven without silently changing the original primary family.

| Order | `context_id` | Plain name | C3 role |
|---:|---|---|---|
| 1 | `astrocytes` | Astrocytes | Primary confirmatory |
| 2 | `excitatory_neurons` | Excitatory neurons | Primary confirmatory |
| 3 | `inhibitory_neurons` | Inhibitory neurons | Primary confirmatory |
| 4 | `immune_cells` | Immune cells | Secondary extension |
| 5 | `opcs` | Oligodendrocyte precursor cells | Secondary extension |
| 6 | `oligodendrocytes` | Oligodendrocytes | Secondary extension |
| 7 | `vasculature` | Vasculature cells | Secondary extension |

Secondary-context results are reported fully. They cannot rescue a failed
primary C3 decision. Before execution, the team may instead approve all seven
as one confirmatory family, but that would be a new frozen analysis version
with 21 general and 147 modifier primary tests. It must not be decided after
effects are viewed.

Phase 15 does not compare these contexts directly. Passing in astrocytes and
failing in neurons does not prove that astrocytes and neurons differ.

### Two frozen respiratory modules

| Order | `module_id` | Reference size | Role in C3 |
|---:|---|---:|---|
| 1 | `mtdna_oxphos_13` | 13 | mtDNA side of the relationship |
| 2 | `nuclear_oxphos_structural_86` | 86 | Nuclear side of the relationship |

The production source of truth is the matching 99 membership rows in:

```text
config/phase13_respiratory_modules.tsv
```

Translation, MIB/MICOS, ATP synthase, mitophagy, and additional mitochondrial
programs are not part of the C3 endpoint. They cannot be added after looking at
Phase 15 results.

Both modules must pass their Phase 13 context-specific admitted-gene coverage
rules. Phase 15 preserves that full-data admitted membership during every
resample. It may recalculate normalization and NCI reference parameters, but it
must not select a different gene list in a favorable resample.

### Twelve diagnosis, sex, and APOE groups

Phase 15 inherits these 12 groups exactly from Phase 13:

```text
NCI__Female__e2       AD__Female__e2
NCI__Female__e33      AD__Female__e33
NCI__Female__e4       AD__Female__e4
NCI__Male__e2         AD__Male__e2
NCI__Male__e33        AD__Male__e33
NCI__Male__e4         AD__Male__e4
```

The six sex-by-APOE strata are:

```text
Female__e2   Female__e33   Female__e4
Male__e2     Male__e33     Male__e4
```

Here, e33 means APOE ε3/ε3. The e2 and e4 definitions must be inherited from
Phase 02 and Phase 13. `projid` remains a character identifier.

### Seven inherited modifier contrasts

For endpoint `Y`, sex `s`, APOE group `a`, and context `c`, define:

```text
DeltaY(s,a,c) = adjusted mean Y in AD - adjusted mean Y in NCI
```

The seven direct modifier contrasts are:

| Order | `contrast_id` | Exact comparison |
|---:|---|---|
| 1 | `sex_F_minus_M__e2` | `DeltaY(Female,e2) - DeltaY(Male,e2)` |
| 2 | `sex_F_minus_M__e33` | `DeltaY(Female,e33) - DeltaY(Male,e33)` |
| 3 | `sex_F_minus_M__e4` | `DeltaY(Female,e4) - DeltaY(Male,e4)` |
| 4 | `apoe_e2_minus_e33__Female` | `DeltaY(Female,e2) - DeltaY(Female,e33)` |
| 5 | `apoe_e2_minus_e33__Male` | `DeltaY(Male,e2) - DeltaY(Male,e33)` |
| 6 | `apoe_e4_minus_e33__Female` | `DeltaY(Female,e4) - DeltaY(Female,e33)` |
| 7 | `apoe_e4_minus_e33__Male` | `DeltaY(Male,e4) - DeltaY(Male,e33)` |

Positive means that the AD-related endpoint change is more positive, or less
negative, in the first named group. Negative means that it is more negative,
or less positive, in the first named group.

For the slope endpoint, `DeltaY` means the AD-minus-NCI change in the
mtDNA-versus-nuclear slope. The same seven difference-of-differences are then
applied to those slope changes.

Every coefficient vector must be inherited from Phase 13 and verified with a
small hand-calculated example.

### Covariates

Primary models adjust for:

```text
age_death_scaled
pmi_scaled
study
```

The general estimand averages six model-based recorded-sex-by-APOE stratum
effects equally. The NCI reference model includes the same six-level stratum
factor so that sex-by-APOE reference differences are not forced to be additive.

`study` distinguishes the ROS and MAP parent studies. It is required because
study membership is not balanced equally across all diagnosis, sex, and APOE
groups.

Use the Phase 02 scaling and coding exactly. Do not recalculate age or PMI
scaling within a context, group, fold, or resample.

Percent mitochondrial reads is not a primary covariate. It is mathematically
related to the mtDNA outcome and can remove the signal by construction. It is
reported as an artifact diagnostic. Independently defined Phase 13 QC flags
and a normalization sensitivity are used for the mandatory technical checks.

Do not invent RIN, batch, or other unavailable fields.

### Primary score pair

For each donor `d` and context `c`, Phase 15 uses:

```text
M(d,c) = Phase 13 standardized mtDNA OXPHOS score
N(d,c) = Phase 13 standardized nuclear OXPHOS score
```

Both are in context-specific NCI standard-deviation units. Their pooled NCI
means are zero apart from rounding.

Phase 15 must reconstruct these scores exactly from the Phase 13 expression
bundle and NCI reference parameters before accepting them as inputs. A mismatch
beyond the frozen numeric tolerance is blocking.

Scores are calculated separately within each context. A score of `1` in
astrocytes and a score of `1` in excitatory neurons have a similar standardized
meaning but are not the same biological measurement. Phase 15 does not subtract
one context's score from another.

### Endpoint 1: standardized compartment difference

For donor `d` and context `c`, calculate:

```text
D(d,c) = M(d,c) - N(d,c)
```

Interpretation:

- positive `D`: mtDNA expression is relatively higher than nuclear OXPHOS;
- negative `D`: mtDNA expression is relatively lower than nuclear OXPHOS;
- zero: the two NCI-standardized compartment scores are equal.

Do **not** standardize this difference a second time. `M` and `N` have already
been centered and scaled by their Phase 13 context-specific NCI references.
One unit of `D` is therefore one mtDNA-score unit minus one nuclear-score unit,
where each input unit is its own pooled-NCI standard deviation. This preserves
the endpoint definition in the existing C3 companion document.

This endpoint detects a relative level imbalance. It does not by itself prove
that the slope connecting the two scores changed.

### Endpoint 2: cross-fitted NCI-reference residual

Within each context, use eligible NCI donors to estimate:

```text
M ~ N
    + sex_APOE_stratum
    + age_death_scaled
    + pmi_scaled
    + study
```

Then calculate:

```text
R_raw(d,c) = observed M(d,c) - NCI-reference predicted M(d,c)
```

Interpretation:

- positive residual: mtDNA expression is higher than predicted;
- negative residual: mtDNA expression is lower than predicted.

#### Why cross-fitting is required

An NCI donor must not help fit the same model used to predict that donor. Phase
15 uses deterministic five-fold donor-level cross-fitting:

1. within each context, sort NCI donors using the frozen seed and stable donor
   ID: within each `sex × APOE × study` block, calculate a SHA-256 value from
   `base_seed + context_id + projid` and sort by that value;
2. assign the sorted donors cyclically to folds 1–5, rotating the starting fold
   by the frozen block order so the total fold sizes remain balanced;
3. fit the NCI model on four folds;
4. predict the held-out NCI fold;
5. predict every AD donor from each of the five NCI training models; and
6. use the mean of the five AD predictions.

No AD donor is used to fit the NCI reference. Every NCI residual is based on a
model that did not contain that donor.

The Phase 13 score scale is a frozen measurement definition. Primary
cross-fitting applies to the NCI relationship model above; it does not change
the full-data admitted gene lists or re-estimate a different score scale in
each fold. The score transformation was fixed upstream without using Phase 15
AD effects; changing its units by fold would make held-out and ensemble
residuals incomparable. Whole-donor bootstrap still rebuilds the score scale
once within each complete resample under the frozen Phase 13 procedure.

Every training fold must retain a full-rank design, both studies, and all six
recorded-sex-by-APOE strata. If five-fold cross-fitting cannot meet those
requirements, the residual endpoint is `not_testable` for that context. The
script may not silently reduce the number of folds after results are seen.

Standardize the raw residual using the cross-fitted NCI residual distribution:

```text
R(d,c) = [R_raw(d,c) - mean_NCI(R_raw,c)] / SD_NCI(R_raw,c)
```

The primary result uses `R`. Save `R_raw`, every prediction, every fold, and
all model coefficients. A full-sample NCI fit is a required sensitivity, not a
replacement for the cross-fitted primary endpoint.

This residual is the planned **candidate bridge outcome** in later phases. It
cannot serve as that bridge merely because it is calculated. The matching C3
gate and the residual endpoint itself must pass first.

### Endpoint 3: coupling-slope change

The slope asks how much the mtDNA score changes when the nuclear score changes
by one NCI standard deviation.

Do not compare:

```text
AD correlation is significant
NCI correlation is not significant
```

That is not a direct comparison. Phase 15 fits one model containing the direct
slope interaction.

Interpretation of a slope-change estimate:

- positive: the mtDNA-versus-nuclear slope is more positive, or less negative,
  in AD;
- negative: the slope is less positive, or more negative, in AD.

A slope change can cross zero or change differently across the nuclear-score
range. Its numeric sign is therefore not automatically equivalent to the sign
of a difference or residual effect.

### General C3 models

General C3 asks for the average AD-minus-NCI change across the six recorded
sex-by-APOE strata. The six strata receive equal weight. This makes the target
quantity explicit and prevents a large stratum from dominating the answer.

For `D` and `R`, fit separately in each context:

```text
endpoint
    ~ 0
      + diagnosis_sex_APOE_group
      + age_death_scaled
      + pmi_scaled
      + study
```

First calculate the adjusted AD-minus-NCI effect within each of the six
sex-by-APOE strata. The primary general estimate is:

```text
general AD effect = (1/6) * sum of the six stratum AD-minus-NCI effects
```

Its standard error and confidence interval must use the full fitted covariance
matrix. It is not the arithmetic average of six separately fitted estimates.

For the slope endpoint, use the saturated group-specific slope model defined
below. First calculate the AD-minus-NCI slope change within each stratum, then
take the same equal-weight one-sixth marginal contrast. This remains the
general estimand even when the six stratum effects differ.

The simpler common-diagnosis/common-slope models are optional model diagnostics
only. They cannot replace the frozen equal-stratum primary contrast.

For each context and endpoint, fit the saturated model once. Extract the
equal-weight general contrast and all seven modifier contrasts from that same
fit and covariance matrix. The separate general and modifier result files are
organizational; they must not come from incompatible refits.

### Modifier-specific C3 models

For `D` and `R`, fit separately in each context:

```text
endpoint
    ~ 0
      + diagnosis_sex_APOE_group
      + age_death_scaled
      + pmi_scaled
      + study
```

Apply the exact seven Phase 13 contrast vectors.

For the slope endpoint, fit:

```text
M
    ~ 0
      + diagnosis_sex_APOE_group
      + 0 + N:diagnosis_sex_APOE_group
      + age_death_scaled
      + pmi_scaled
      + study
```

Let `b(g,c)` be the fitted nuclear-score slope for one of the 12 groups. For
one sex/APOE stratum:

```text
slope AD effect = b(AD,stratum,c) - b(NCI,stratum,c)
```

For female-versus-male within e4, the direct slope modifier is:

```text
[b(AD,Female,e4) - b(NCI,Female,e4)]
-
[b(AD,Male,e4) - b(NCI,Male,e4)]
```

Derive all seven contrasts from exact model covariance. Do not fit separate AD
and NCI correlations and compare their P values.

### Estimation and covariance

Use ordinary least squares with the HC3 heteroskedasticity-robust covariance
matrix:

```r
fit <- stats::lm(formula, data = analysis_data)
V <- sandwich::vcovHC(fit, type = "HC3")
```

For coefficient or contrast vector `c`:

```text
estimate = c' beta
SE       = sqrt(c' V c)
df       = number of fitted donor profiles - rank(design)
t        = estimate / SE
P        = 2 × Pr[T(df) >= absolute t]
95% CI   = estimate ± t_(0.975,df) × SE
```

All tests are two-sided. Use the version of `sandwich` pinned in `renv.lock`.
Do not switch covariance type, reference distribution, degrees of freedom, or
interval formula after seeing results.

Save ordinary Pearson and Spearman correlations by group for explanation only.
They are not C3 tests and cannot replace the direct slope interaction.

### Planned result grids

The confirmatory primary grids are:

```text
general C3:
    3 endpoints × 3 primary contexts = 9 tests

modifier-specific C3:
    3 endpoints × 7 modifiers × 3 primary contexts = 63 tests
```

The secondary grids are:

```text
secondary general C3:
    3 endpoints × 4 secondary contexts = 12 tests

secondary modifier-specific C3:
    3 endpoints × 7 modifiers × 4 secondary contexts = 84 tests
```

The complete production bundle therefore contains:

```text
general endpoint rows: 9 + 12 = 21
modifier endpoint rows: 63 + 84 = 147
general context gates: 7
modifier context-by-contrast gates: 7 × 7 = 49
```

For interpretation, also save:

```text
7 contexts × 6 strata × 3 endpoint types = 126 stratum rows
```

For `D` and `R`, a stratum row is the adjusted AD-minus-NCI endpoint effect.
For the slope endpoint, it is the AD-minus-NCI difference in the fitted slope.
These 126 rows explain the direct contrasts; they are not another C3 testing
family.

Every structural row must be written before eligibility filtering. Untestable
rows remain present with `p = NA`, `q = NA`, and an exact reason.

### Multiple-testing correction

Freeze four Benjamini-Hochberg families:

| Family ID | Content | Expected rows |
|---|---|---:|
| `M15-general-primary` | 3 endpoints × 3 primary contexts | 9 |
| `M15-modifier-primary` | 3 endpoints × 7 modifiers × 3 primary contexts | 63 |
| `M15-general-secondary` | 3 endpoints × 4 secondary contexts | 12 |
| `M15-modifier-secondary` | 3 endpoints × 7 modifiers × 4 secondary contexts | 84 |

Apply BH once to all testable raw P values within each complete family.
Untestable rows remain in the family manifest with missing P and q values.

Do not correct only within an attractive context, endpoint, modifier, sex, or
APOE group. A secondary q value cannot substitute for a primary-family result.

### Donor and context eligibility

Inherited profile rules are:

- primary profile: at least 20 nuclei in the donor/context broad aggregate;
- sensitivity profile: at least 50 nuclei;
- no imputation of a missing donor/context profile;
- both respiratory modules pass Phase 13 admitted-gene coverage; and
- metadata, score, and count keys agree exactly.

The Phase 13 full-data admitted genes remain fixed in all Phase 15 resamples.

### NCI-reference eligibility

The cross-fitted residual is estimable only when, within a context:

- at least 30 eligible NCI donors are available;
- the full NCI reference has at least 20 residual degrees of freedom;
- both recorded sexes, all available APOE groups, and both studies occur;
- every one of the five training designs is full rank;
- `N` has finite nonzero variance;
- all predictions are finite; and
- the cross-fitted NCI residual SD is positive and finite.

At least 50 eligible NCI donors are required for an internally confirmatory
residual result, whether that residual is used in a general or a
modifier-specific gate. A 30–49-donor NCI reference can produce only a
`provisional_low_power` residual even if every other rule passes. This
reference count is context-wide and is separate from the four-cell count rule
for a modifier contrast.

### General-test eligibility

A general endpoint is estimable only when:

- at least 20 eligible AD donors and 30 eligible NCI donors are available;
- every sex-by-APOE stratum needed by the adjustment is represented;
- the design is full rank with at least 20 residual degrees of freedom; and
- endpoint-specific variance, prediction, and range checks pass.

Internal confirmation requires at least 30 AD donors, at least 50 NCI donors,
and at least three AD and three NCI donors in each of the six sex-by-APOE
strata. Counts below those confirmation rules but above the estimation rules
are labeled provisional rather than supported.

### Modifier-test eligibility

Each modifier requires four diagnosis-by-group cells:

- fewer than 5 donors in any required cell: `not_testable`;
- 5–9 donors in any required cell: estimable but at most
  `provisional_low_power`;
- at least 10 donors in all four cells: eligible for internal support.

Male e2 has only about six NCI and seven AD donors in the global cohort. An e2
modifier involving male e2 therefore cannot become internally confirmatory
under the current donor rule, even if its estimated effect is large.

### Additional slope eligibility

A slope endpoint additionally requires:

- finite nuclear-score variance in every diagnosis/group used by the test;
- at least five distinct nuclear-score values per required group;
- finite HC3 covariance and positive residual degrees of freedom;
- no model rank deficiency;
- adequate shared predictor support; and
- no conclusion outside the shared nuclear-score range.

For each required pair of groups, calculate overlap of the central 90% nuclear
score intervals. A confirmatory slope requires an overlap fraction of at least
`0.50`, where overlap is divided by the shorter central interval. Below `0.50`,
the slope row is `inconclusive_range_mismatch` or `not_testable` if no interval
overlap exists.

This `0.50` threshold is a proposed project rule. It must be approved before
results are opened.

### Smallest effects considered meaningful

Freeze these proposed smallest effects of interest, called SESOIs:

| Endpoint | Proposed SESOI | Unit |
|---|---:|---|
| `standardized_difference` | 0.25 | Difference between the two Phase 13 NCI-standardized score units |
| `nci_reference_residual` | 0.25 | NCI cross-fitted residual SD |
| `coupling_slope_change` | 0.25 | mtDNA NCI SD per nuclear OXPHOS NCI SD |

These values are project decision rules, not universal biological constants.
They must be approved before Phase 15 estimates are opened.

An endpoint meets the positive effect rule when:

```text
q <= 0.05
AND absolute estimate >= endpoint SESOI
AND the 95% CI excludes zero
```

A precise no-meaningful-effect result requires the entire 95% CI to lie inside
the matching interval:

```text
[-0.25,+0.25]
```

A q value above 0.05 is not automatically a precise null.

### Direction compatibility across endpoints

The difference and residual are both relative-level measurements. If both pass,
their signs must agree.

`D` and `R` are correlated transformations of the same two donor scores. They
are corroborating views of one RNA-expression relationship, not independent
replications.

The slope measures the shape of the relationship, so its numeric sign is not
forced to match the difference or residual sign. When the slope contributes to
a C3 pass:

1. calculate the fitted AD-minus-NCI departure at nuclear scores `-1`, `0`, and
   `+1`;
2. for modifier C3, calculate the corresponding direct difference between the
   two modifier groups at the same three points;
3. require agreement with the passing level endpoint at at least two points;
4. require no reversal inside the central shared predictor range; and
5. save the complete prediction grid rather than only the three checkpoints.

A stable crossing-slope result is scientifically interesting but does not meet
the frozen Gate 2 compatibility rule. Report it separately as
`slope_rewiring_observed`, show the crossing point, and do not count it as one
of the two gate-carrying endpoints. A later approved analysis version could
define a separate non-directional shape-change claim; Phase 15 may not create
that claim after inspecting results.

No analyst may assign compatibility by visually inspecting a plot. The frozen
calculation writes the compatibility fields automatically.

### Frozen prediction grid used for slope compatibility

Predictions must not depend on an analyst's plotting choices. Within each
context:

1. define the common nuclear-score interval as the intersection of the central
   90% ranges for the groups required by that test;
2. evaluate 41 equally spaced values across that interval, including the
   nearest available points to `-1`, `0`, and `+1` when those values lie inside
   the interval;
3. set `age_death_scaled = 0` and `pmi_scaled = 0`;
4. predict once for ROS and once for MAP, then average the two predictions with
   equal one-half weights;
5. for general C3, average the six stratum-specific AD departures with equal
   one-sixth weights; and
6. for modifier C3, use the exact named strata and the frozen direct
   difference-of-differences.

If fewer than two of `-1`, `0`, and `+1` lie within the common interval, use the
25th, 50th, and 75th percentiles of that interval as the three compatibility
checkpoints and record `checkpoint_substitution = TRUE`. All grid coordinates,
covariate values, study weights, and stratum weights are saved.

## Stability and sensitivity analyses

Every estimable general and modifier endpoint row receives the planned checks.
Do not run them only for rows that first appear significant.

### A. Whole-donor bootstrap

Run 1,000 production repetitions.

For each repetition:

1. resample whole donors with replacement within all 12 diagnosis, sex, and
   APOE groups;
2. give every sampled copy a unique bootstrap-draw ID while retaining its
   original donor ID for provenance;
3. carry all available contexts for that donor together;
4. reconstruct TMM normalization from the Phase 13 broad all-gene counts;
5. keep the full-data admitted module genes fixed;
6. recalculate NCI gene means, gene SDs, module means, and module SDs;
7. rebuild both donor scores;
8. rebuild deterministic cross-fitting folds and residual references, assigning
   folds from the **original donor ID**, not the bootstrap-draw ID;
9. recalculate all three endpoints and refit all eligible models; and
10. save every estimate and failure reason.

All bootstrap copies of the same original donor must remain in the same
cross-fitting fold. For every fold, the set of original donor IDs in training
must be disjoint from the set in held-out prediction. Unique bootstrap-draw IDs
prevent duplicate matrix columns, but they are never used to bypass this
leakage check.

For every endpoint row, save:

- primary estimate;
- bootstrap median;
- percentile 95% interval;
- successful repetitions;
- same-sign repetitions;
- sign-retention fraction; and
- every model/reference failure count.

A supported endpoint requires:

```text
at least 950 of 1,000 repetitions succeed
AND at least 80% of successful estimates retain the primary sign
```

Bootstrap significance is not used as a second P-value gate. It measures
stability.

### B. Leave one donor out

Remove one donor and all of that donor's contexts. Rebuild normalization,
scores, cross-fitted residuals, and models.

A supported endpoint can have no leave-one-donor-out sign reversal:

```text
primary estimate × leave-one-donor-out estimate < 0
```

Also save the largest absolute change and the donor producing it. A stable sign
does not make a very wide interval conclusive.

### C. Group-size-balanced resampling

Run 1,000 production repetitions.

For a general test:

1. work within one context;
2. within each of the six sex-by-APOE strata, downsample the larger diagnosis
   group to the smaller diagnosis count;
3. retain all six strata; and
4. rebuild normalization, both scores, the NCI reference, and all endpoints;
   and
5. fit the frozen saturated model and equal-weight general contrast.

For a modifier test:

1. work within one context and one modifier;
2. downsample its four required diagnosis-by-group cells to the smallest cell;
3. retain the other eight diagnosis-by-sex-by-APOE groups unchanged so the
   frozen score and NCI-reference procedures remain estimable;
4. rebuild normalization, both scores, the NCI reference, and all endpoints;
5. refit the frozen saturated 12-group endpoint or group-slope model with age,
   PMI, and study; and
6. apply the same four-term contrast.

Balancing is defined separately for each `context × contrast` donor pool. A
donor can therefore be retained in one context's balanced repetition and not
another's. This analysis does not claim to preserve paired contexts. Do not
discard the eight non-required groups and then fit the 12-level model; that
would be rank deficient.

At least 950 repetitions must succeed and at least 80% of successful estimates
must retain the direction for a supported row.

### D. Fifty-nucleus sensitivity

Repeat the entire analysis using only donor/context profiles with at least 50
nuclei.

When estimable, a supported endpoint requires:

- the same direction; and
- at least 50% of the primary absolute magnitude.

If the 50-nucleus result is untestable because too many donors are lost, label
the sensitivity `not_testable`. It is not a contradictory null, and the C3 gate
is inconclusive rather than supported.

This is an eligibility sensitivity, not exact nucleus-depth equalization.
Phase 15 does not read individual nuclei and cannot claim that exact nucleus
depth was balanced.

### E. NCI-trained PC1 score sensitivity

Use the Phase 13 NCI-trained, oriented, and NCI-SD-standardized PC1 scores for
both compartments:

```text
M_PC1 = PC1 score for mtdna_oxphos_13
N_PC1 = PC1 score for nuclear_oxphos_structural_86
```

Rebuild all three Phase 15 endpoints and models. Do not mix a mean-z score on
one side with a PC1 score on the other.

For a supported endpoint, the PC1 estimate must retain the direction and at
least 50% of the primary standardized magnitude when estimable. Both Phase 13
module reliability correlations must be at least `0.70` in the matching
context.

PC1 cannot rescue a failed primary mean-z result.

### F. NCI-reference sensitivity

The residual endpoint receives these required checks:

1. repeat five-fold cross-fitting under 50 additional deterministic fold
   assignments;
2. require at least 80% of assignment-specific effects to retain the primary
   direction;
3. fit the full NCI reference without cross-fitting and compare estimates;
4. fit an additive `sex + apoe_group` reference as a sensitivity to the primary
   six-level sex-by-APOE-stratum reference;
5. report fold coefficients, prediction errors, leverage, and out-of-range
   predictions.

The primary result remains the originally frozen fold assignment. Repeated
assignments test sensitivity to the arbitrary fold split.

### G. Mitochondrial-composition normalization sensitivity

The two scores come from the same RNA library. Shared library composition can
create or distort correlation.

Recalculate TMM normalization factors using the full filtered nuclear
transcriptome after excluding every chromosome-M/mtDNA feature. Apply those
frozen factors to the full count matrix, including the 13 mtDNA genes, then
rebuild both scores and all endpoints.

A supported endpoint must retain its direction. This sensitivity tests whether
mtDNA genes influenced their own library normalization.

It does not remove all possible compositional effects, so the final discussion
must retain this limitation.

### H. Gene and complex influence

Run the following fixed checks:

1. remove each of the 13 mtDNA genes one at a time;
2. remove each nuclear OXPHOS complex I–V one at a time;
3. remove the four nuclear Complex II genes, producing an 82-gene nuclear set
   restricted to complexes I, III, IV, and V; and
4. run focused matched-complex analyses for complexes I, III, IV, and V.

Complex II has no mtDNA-encoded structural subunit. The 86-gene nuclear score
remains primary for continuity with Phase 13; the 82-gene version asks whether
Complex II changes the conclusion.

A supported endpoint requires:

- at least 12 of 13 mtDNA leave-one-gene-out estimates to retain direction;
- at least 4 of 5 nuclear leave-one-complex-out estimates to retain direction;
- no omission to produce an opposite effect meeting the endpoint SESOI; and
- the 82-gene nuclear sensitivity to retain direction.

Matched-complex results localize the signal. Because they reuse genes from the
primary modules, they are not independent confirmations and cannot rescue C3.

### I. Slope diagnostics and nonlinear sensitivity

For every slope row:

1. save group-specific slopes, Pearson correlations, and Spearman correlations;
2. save nuclear-score ranges, central 90% intervals, and overlap fractions;
3. trim to the shared predictor range and refit;
4. fit a prespecified quadratic sensitivity using `N + N^2` and the matching
   diagnosis/group interactions;
5. plot and save model-predicted values over the shared score grid; and
6. report leverage, Cook's distance, residual patterns, and influential donors.

A linear slope claim is blocked when the quadratic term reveals a stable
relationship shape that makes the single slope misleading, the common-range
trim reverses direction, or the result depends on extrapolation.

A reproducible crossing relationship is labeled `slope_rewiring_observed` and
reported outside Gate 2. It is not forced into higher/lower imbalance wording
and cannot make C3 pass in this analysis version.

### J. QC sensitivities

Repeat the endpoint models after:

- excluding profiles whose Phase 13 `robust_qc_fraction` is at least the frozen
  severe-QC threshold of `0.50`;
- adding `robust_qc_fraction` as a sensitivity covariate; and
- adding aggregate percent mitochondrial reads as a diagnostic covariate.

Severe-QC exclusion is mandatory and must retain direction. Percent-mt
adjustment is reported but is not an automatic veto because percent-mt is
mathematically coupled to the mtDNA score. A major reversal after percent-mt
adjustment is labeled `mt_fraction_sensitive` and discussed explicitly.

Unavailable RIN or batch variables are not silently added.

### K. Technical negative controls

Use synthetic null fixtures and, only for within-stratum slope/covariance code,
fixed donor-pair permutations to verify that:

- pairing mtDNA from one donor with nuclear expression from another within the
  same diagnosis-by-sex-by-APOE stratum removes the intended donor-level
  slope/covariance signal in the fixture;
- the cross-fitting code never includes a held-out NCI donor in its training
  data;
- contrast signs reproduce hand calculations; and
- null fixtures do not systematically pass Gate 2.

These are implementation checks, not biological tests. A donor-pair
permutation is not expected to erase a real group-level mean difference and is
never used as evidence against a `D` or `R` result.

## Phase 15 C3 gates

Technical validation and scientific support are separate. A technically
complete Phase 15 run may contain no supported C3 result.

### Endpoint-level status

Assign one status to every one of the 21 general and 147 modifier endpoint
rows, in this order:

1. `not_testable` when required inputs, coverage, counts, variance, rank,
   reference fitting, range overlap, covariance, or model convergence prevent
   estimation;
2. `provisional_low_power` when every non-count support rule passes but the
   frozen confirmation count is not met;
3. `supported` when q, effect, CI, eligibility, and every mandatory stability
   rule pass;
4. `statistically_detectable_but_small` when q and nonzero-CI rules pass but
   the absolute estimate is below the endpoint SESOI;
5. `not_supported_precise_null` when the full 95% CI is inside the endpoint
   SESOI interval; and
6. `inconclusive` otherwise.

Store every component as a separate Boolean or status field. The summary label
must never hide why a row passed or failed.

### Gate 2A: general C3 within one context

A context receives `supported` general C3 status only when all conditions hold:

1. at least two of the three general endpoint rows are `supported` in the
   matching family;
2. at least one supported endpoint is the NCI-reference residual or the slope;
3. the frozen compatibility rule for the selected pair of carrier endpoints
   passes;
4. both respiratory modules pass coverage and reliability;
5. every endpoint carrying the gate passes its general donor-count rule; if
   the residual carries the gate, its NCI reference also has at least 50
   eligible NCI donors and passes every reference check;
6. bootstrap, leave-one-donor-out, balancing, 50-nucleus, PC1,
   normalization, reference, gene/complex, QC, and slope-specific checks pass
   for every endpoint used by the gate, with reference checks required only
   when the residual carries the gate and slope checks only when the slope
   carries the gate; and
7. no blocking provenance or technical check fails.

Gate 2A is `provisional_low_power` when at least two carrier endpoints have
status `supported` or `provisional_low_power`, at least one carrier is
`provisional_low_power`, at least one carrier is the residual or slope, and all
non-count gate rules above pass. This is the executable meaning of “the same
scientific pattern passed but a count rule did not.”

### Gate 2B: modifier-specific C3

A context-by-modifier row receives `supported` status only when:

1. at least two of its three modifier endpoint rows are `supported` in the
   matching modifier family;
2. at least one is the residual or slope;
3. endpoint compatibility passes;
4. all four required diagnosis-by-group cells have at least 10 donors;
5. if the residual carries the gate, its context-wide NCI reference has at
   least 50 eligible donors and passes every reference check;
6. all endpoint-specific stability and technical rules pass; and
7. no blocking provenance check fails.

A Gate 2B row is `provisional_low_power` when at least two carrier endpoints
have status `supported` or `provisional_low_power`, at least one carrier is
`provisional_low_power`, at least one carrier is the residual or slope, and all
non-count rules pass. A 5–9-donor modifier cell or a 30–49-donor NCI residual
reference can therefore produce only a provisional gate. This is especially
important for e2 comparisons involving male e2.

General C3 does not need to pass before a modifier-specific C3 contrast can be
estimated. Opposite group effects can cancel in the general average. If the
modifier gate alone passes, the wording must say that the AD-related
relationship **differed between the exact groups**; it must not claim a common
overall AD shift.

### Compatibility classifications

For every supported or provisional C3 gate, assign one:

| Classification | Required endpoint pattern | Permitted interpretation |
|---|---|---|
| `relative_imbalance` | Difference + residual pass; slope does not carry the gate | Altered relative mitonuclear expression balance/departure |
| `slope_change` | Slope + one compatible level endpoint pass | Altered mitonuclear coupling slope |
| `imbalance_and_slope_change` | All three pass compatibly | Both relative imbalance and slope change |

Do not use “decoupling” for a difference-plus-residual result. Reserve slope
language for a passing slope endpoint.

`slope_rewiring_observed` is a separate descriptive flag, not a Gate 2
classification. A crossing slope cannot help a C3 gate pass in this analysis
version.

### Bridge authorization for later candidate tests

The NCI-reference residual is the planned shared bridge outcome for later
candidate-system work.

Set `bridge_authorized = TRUE` only when:

1. the matching Gate 2A or Gate 2B C3 decision passes;
2. the residual endpoint itself is `supported` for the exact context and
   general/modifier comparison;
3. the residual reference and cross-fold sensitivities pass; and
4. the endpoint definition remains the full frozen 13-versus-86 relationship.

C3 can pass using the difference and slope while the residual does not pass.
In that case, C3 wording may be allowed, but the residual is not authorized as
the candidate convergence bridge.

### Gate-level statuses

Use exactly one status for each of the 7 general context gates and 49 modifier
context-by-contrast gates. Apply the following rules in order:

1. `not_testable` when a blocking shared input/module/provenance failure exists
   or none of the three endpoints can be estimated;
2. `supported` when the relevant Gate 2A or 2B supported rule passes;
3. `provisional_low_power` when its explicit two-carrier provisional rule
   passes;
4. `partial_evidence` when at least one endpoint is supported/provisional but
   there are not two valid compatible carriers, or two otherwise eligible
   endpoints disagree;
5. `not_supported_precise_null` when all three endpoints are estimable, all
   three confidence intervals lie inside their SESOI ranges, and none passes;
6. `inconclusive` for every remaining mixture of wide intervals, instability,
   incomplete sensitivities, or endpoint-specific untestability.

| Status | Meaning |
|---|---|
| `supported` | At least two required endpoints and every gate rule passed |
| `provisional_low_power` | Biological and stability rules passed, but confirmation counts did not |
| `partial_evidence` | One endpoint passed, or two passed without the required residual/slope or compatibility |
| `not_supported_precise_null` | All estimable endpoint intervals lie inside their SESOI ranges and none passes |
| `inconclusive` | Available intervals or stability cannot distinguish a meaningful effect from no effect |
| `not_testable` | Too little valid information exists to apply Gate 2 |

A gate is `not_supported_precise_null` only under the exact all-three-endpoint
rule above. One wide or missing endpoint makes the gate inconclusive unless a
supported/provisional endpoint makes it `partial_evidence`.

### Overall primary C3 decision

The production bundle stores one of:

```text
supported_general_and_modifier
supported_general_only
supported_modifier_only
provisional
not_supported
inconclusive
not_testable
```

Only the three primary contexts determine this overall label. Secondary-only
support is recorded separately as `secondary_context_support_only` and cannot
change a failed or inconclusive primary label.

Apply the overall labels in this exact order:

1. `supported_general_and_modifier` if at least one primary general gate and at
   least one primary modifier gate are `supported`;
2. `supported_general_only` if at least one primary general gate is supported
   and no primary modifier gate is supported;
3. `supported_modifier_only` if at least one primary modifier gate is supported
   and no primary general gate is supported;
4. `provisional` if no primary gate is supported but at least one is
   `provisional_low_power`;
5. `not_testable` if every primary gate is `not_testable`;
6. `not_supported` if at least one confirmation-eligible primary gate exists,
   every such gate is `not_supported_precise_null`, and none is
   `partial_evidence` or `inconclusive`; structurally low-power gates are
   reported but cannot overturn this label unless they are provisional; and
7. `inconclusive` for every remaining mixture.

Thus one wide interval, unstable carrier, or incomplete mandatory sensitivity
in a confirmation-eligible primary gate prevents a `not_supported` conclusion.

### Allowed wording

If difference and residual pass without slope:

> In ROSMAP donor-level [context] profiles, AD was associated with an altered
> relative balance between mtDNA-encoded respiratory and nuclear-encoded
> OXPHOS structural-gene expression.

If the general slope gate passes:

> In ROSMAP donor-level [context] profiles, AD was associated with an altered
> mtDNA-versus-nuclear OXPHOS expression slope.

If a modifier gate passes:

> In ROSMAP donor-level [context] profiles, the AD-related mitonuclear
> expression relationship differed between [exact first group] and [exact
> second group].

Every sentence must name the context, endpoint classification, comparison,
direction, donor counts, and internal ROSMAP status.

Do not say:

- mitochondrial function failed;
- ATP production decreased;
- mtDNA copy number changed;
- one gene caused the relationship;
- the effect was specific to one context; or
- the result was independently replicated.

If Phase 15 modifier C3 passes but Phase 13 C1 does not, report the coupling
modifier result by itself. Do not also claim that sex or APOE modified the
average respiratory-program abundance unless the matching C1 gate passed.

## Inputs and dependencies

### Required Phase 13 production state

Phase 15 requires:

```text
results/minerva_production/13_respiratory_modifier/
```

with `respiratory_status.tsv` reporting:

```text
validation_status = validated_complete
contexts = 7
modules = 4
module_memberships = 273
modifier_contrasts = 7
planned_primary_tests = 196
```

Every blocking Phase 13 check and every declared input/output hash must validate
independently. Directory existence is not sufficient.

### Current repository readiness

As of 2026-08-08, the repository contains:

```text
config/phase13_respiratory_modifier.yml
config/phase13_respiratory_modules.tsv
scripts/13_run_respiratory_modifier.R
tests/test_phase13_respiratory_modifier.R
```

The frozen Phase 13 module membership file contains the exact 13 mtDNA and 86
nuclear OXPHOS genes needed by Phase 15.

However, these required production directories are not currently present in
the shared workspace:

```text
results/minerva_production/07_pseudobulk/
results/minerva_production/13_respiratory_modifier/
```

This is a hard execution blocker, not a reason to weaken Phase 15. Production
Phase 07 must first finish for all nine source RDS inputs, and Phase 13 must then
publish a validated production bundle. Phase 15 implementation and synthetic
testing may proceed while those dependencies are prepared; biological Phase 15
production may not.

### Required Phase 13 files

| File | Phase 15 use |
|---|---|
| `respiratory_analysis_manifest.tsv` | Frozen Phase 13 definitions, thresholds, versions, and provenance |
| `respiratory_cell_context_manifest.tsv` | Seven context IDs, order, sources, and roles |
| `respiratory_contrast_manifest.tsv` | Seven modifier vectors and required groups |
| `respiratory_module_manifest.tsv` | Module labels, roles, sizes, and coverage rules |
| `respiratory_module_members.tsv` | Frozen 273 memberships; Phase 15 uses the 99 direct-respiratory rows |
| `respiratory_donor_samples.tsv.gz` | Donor/context groups, nuclei, QC, and eligibility |
| `respiratory_pseudobulk_counts.rds` | All-gene broad counts for reconstruction and resampling |
| `respiratory_expression_bundle.rds` | Tested genes, TMM/logCPM matrices, designs, and normalization factors |
| `respiratory_module_coverage.tsv` | Admitted genes and coverage in each context |
| `respiratory_nci_reference_parameters.tsv.gz` | Phase 13 gene/module NCI scaling parameters |
| `respiratory_donor_module_scores.tsv.gz` | Primary mean-z standardized scores |
| `respiratory_pc1_loadings.tsv.gz` | NCI-trained PC1 score reconstruction and orientation |
| `respiratory_module_reliability.tsv` | Mean-z/PC1 reliability and concentration checks |
| `respiratory_module_results.tsv` | C1 effects for later cross-claim reporting only |
| `respiratory_gate_decisions.tsv` | C1 status for later cross-claim reporting only |
| `respiratory_checks.tsv` | Upstream blocking and nonblocking checks |
| `respiratory_artifacts.tsv` | Phase 13 artifact inventory and hashes |
| `respiratory_status.tsv` | Terminal technical and scientific state |

Phase 13 effect and gate tables cannot select Phase 15 rows. They are joined
only after every Phase 15 gate has been calculated, to prepare the final
claim-to-evidence handoff.

### Required configuration and software

Phase 15 adds:

```text
config/phase15_mitonuclear_coupling.yml
scripts/15_run_mitonuclear_coupling.R
tests/test_phase15_mitonuclear_coupling.R
```

Required R packages already used or pinned by the project include:

- `edgeR` for reconstruction of TMM/logCPM expression;
- `sandwich` for HC3 covariance;
- base `stats` for linear models, prediction, PCA support, and BH correction;
- `yaml` for configuration; and
- the project's existing TSV, gzip, hash, and validation helpers.

No new package may be added after effects are viewed. If robust regression or a
different nonlinear package is added, pin it in `renv.lock`, document the exact
formula and role, rerun synthetic tests, and create a new analysis fingerprint
before execution.

### Explicit non-inputs

The Phase 15 scientific script must not read:

- Phase 08 DEG results;
- Phase 10 similarity results;
- Phase 11 pathway results;
- Phase 12 KDA or network results;
- Phase 14 plans, results, or figures;
- candidate-system result tables;
- fine-cell normalized matrices;
- manually edited result summaries; or
- figures as numerical inputs.

## Construction and analysis workflow

### Task 1: freeze Phase 15 definitions

**Why:**

The result is trustworthy only when the questions and pass rules are written
before the effects are examined.

**Inputs:**

- this approved plan;
- validated Phase 13 manifests; and
- the companion C3 explanation.

**Steps:**

1. freeze the three primary and four secondary contexts in order;
2. inherit the two modules and 99 gene-membership rows;
3. freeze all three endpoint formulas and signs;
4. freeze the general model and seven modifier vectors;
5. freeze the 9-, 63-, 12-, and 84-row FDR families;
6. approve the endpoint SESOIs and interval rules;
7. approve all donor, cross-fitting, range-overlap, stability, and gate rules;
8. freeze software versions, random-number generator, seeds, schemas, and
   output paths;
9. freeze the five-fold assignment procedure and 50 repeated-fold seeds; and
10. set `definitions_approved = TRUE` and `definitions_frozen = TRUE`.

**Outputs:**

```text
config/phase15_mitonuclear_coupling.yml
mitonuclear_analysis_manifest.tsv
mitonuclear_context_manifest.tsv
mitonuclear_endpoint_manifest.tsv
mitonuclear_contrast_manifest.tsv
mitonuclear_module_manifest.tsv
mitonuclear_module_members.tsv
```

**Ready when:**

Every proposed threshold has a numeric value, every sign has a plain-language
meaning, and no field remains `TBD`.

### Task 2: validate the Phase 13 dependency

**Why:**

Phase 15 cannot distinguish biology from corrupted or incomplete upstream data
unless every Phase 13 input is independently checked.

**Inputs:**

- Phase 13 status, checks, artifact manifest, and required files.

**Steps:**

1. require `validation_status = validated_complete`;
2. verify all expected Phase 13 files exist;
3. recompute and compare every declared SHA-256 hash;
4. verify schemas, first-column `schema_version`, row counts, and unique keys;
5. require exactly seven contexts, four modules, 273 memberships, seven
   modifier contrasts, and 196 Phase 13 result rows;
6. select exactly the 13- and 86-gene direct-respiratory memberships;
7. confirm donor IDs, group labels, context labels, covariates, counts, scores,
   and QC fields agree across files;
8. verify Phase 13 blocking checks have no failure; and
9. stop before inference if any required check fails.

**Outputs:**

```text
mitonuclear_input_inventory.tsv
mitonuclear_source_checks.tsv
```

**Ready when:**

Every required Phase 13 file has a reproducible identity and all blocking
checks pass.

### Task 3: reconstruct and pair the two compartment scores

**Why:**

The mtDNA and nuclear scores must belong to the same donor and context and must
reproduce Phase 13 exactly before their relationship is tested.

**Inputs:**

- Phase 13 counts and expression bundle;
- module coverage and NCI reference parameters;
- donor score table; and
- the frozen 99 membership rows.

**Steps:**

1. reconstruct both primary mean-z scores independently;
2. compare reconstructed and stored scores under a frozen numeric tolerance;
3. pair scores by exact `projid + context_id`;
4. reject duplicate keys and do not impute unpaired profiles;
5. join diagnosis, sex, APOE, age, PMI, study, nuclei, and QC fields;
6. apply the 20-nucleus profile threshold;
7. verify both modules pass context-specific coverage;
8. count donors in all 12 groups and at 20- and 50-nucleus thresholds;
9. calculate NCI and AD nuclear-score ranges and variances; and
10. assign technical eligibility without opening endpoint estimates.

**Outputs:**

```text
mitonuclear_donor_eligibility.tsv
mitonuclear_score_pairs.tsv.gz
mitonuclear_score_reliability.tsv
```

**Ready when:**

Every accepted pair has one donor, one context, two finite scores, complete
required metadata, and a reproducible Phase 13 source row.

### Task 4: build the three C3 endpoints

**Why:**

The three measurements capture different parts of the relationship and must be
built without choosing among results.

**Inputs:**

- paired donor scores;
- frozen cross-fitting rules;
- covariates and eligibility; and
- endpoint definitions.

**Steps:**

1. calculate the compartment difference `D = M - N` without a second
   standardization;
2. create deterministic five-fold NCI assignments;
3. fit every fold-specific NCI reference;
4. generate held-out NCI and ensemble AD predictions;
5. calculate and NCI-standardize residuals;
6. create the donor endpoint table;
7. create full-fit reference sensitivity models;
8. create the full prediction grid for later slope compatibility;
9. preserve all failed contexts/folds with reasons; and
10. verify no held-out NCI donor appears in its training set.

**Outputs:**

```text
mitonuclear_crossfit_folds.tsv
mitonuclear_nci_reference_models.tsv
mitonuclear_reference_predictions.tsv.gz
mitonuclear_donor_endpoints.tsv.gz
```

**Ready when:**

Every eligible donor has reproducible `D` and `R` values, and every reference
prediction has a documented training set.

### Task 5: fit general C3 models

**Why:**

General C3 is required to support an overall AD-related mitonuclear statement
that can stand even when no sex/APOE modifier is supported.

**Inputs:**

- endpoints, paired scores, context tiers, and covariates;
- the 21-row general test manifest; and
- frozen model and covariance rules.

**Steps:**

1. write all 21 structural rows before fitting;
2. fit the saturated difference model in each context;
3. fit the saturated residual model in each context;
4. fit the saturated 12-group nuclear-slope model in each context;
5. derive exact estimates, HC3 SEs, CIs, P values, and effect fields;
6. derive the frozen equal-weight average of the six stratum effects from the
   saturated model and its full covariance;
7. calculate group slopes, correlations, ranges, and the general prediction
   grids;
8. initialize the shared group-slope and prediction-grid files;
9. apply BH separately to the 9 primary and 12 secondary P values; and
10. retain untestable rows with exact reasons.

**Outputs:**

```text
mitonuclear_general_test_manifest.tsv
mitonuclear_general_results.tsv
mitonuclear_group_slopes.tsv
mitonuclear_prediction_grid.tsv.gz
mitonuclear_model_diagnostics.tsv
```

**Ready when:**

Exactly 21 general result rows exist and both BH families reproduce from the
saved raw P values.

### Task 6: fit modifier-specific C3 models

**Why:**

A general AD result cannot support the statement that the relationship differs
by sex or APOE. The seven direct modifier contrasts provide that evidence.

**Inputs:**

- donor endpoints and score pairs;
- seven inherited contrast vectors;
- 147-row modifier manifest; and
- frozen models, eligibility, and covariance rules.

**Steps:**

1. write all 147 structural rows before fitting;
2. reuse and verify the exact saturated difference and residual fits from Task
   5 rather than making a scientifically different refit;
3. reuse and verify the exact group-specific nuclear-slope fits from Task 5;
4. calculate six descriptive stratum effects for all endpoint types;
5. derive all seven direct contrasts using exact HC3 covariance;
6. calculate prediction-grid compatibility for every slope contrast;
7. attach four required group counts, nuclear-score ranges, and eligibility;
8. append modifier rows to, then finalize, the shared group-slope and
   prediction-grid files without overwriting the general rows;
9. apply BH separately to the 63 primary and 84 secondary P values; and
10. preserve every low-power, failed, or untestable row.

**Outputs:**

```text
mitonuclear_modifier_test_manifest.tsv
mitonuclear_modifier_results.tsv
mitonuclear_stratum_effects.tsv
mitonuclear_group_slopes.tsv
mitonuclear_prediction_grid.tsv.gz
mitonuclear_model_diagnostics.tsv
```

**Ready when:**

Exactly 147 modifier and 126 stratum rows exist, and both modifier BH families
reproduce.

### Task 7: run all stability analyses

**Why:**

A C3 result is not reliable if one donor, one score formula, one NCI fold, one
normalization choice, or poor predictor overlap creates it.

**Inputs:**

- all frozen endpoint rows;
- Phase 13 counts and fixed admitted genes;
- scores, reference models, and QC data; and
- stability seeds and thresholds.

**Steps:**

1. run 1,000 whole-donor bootstrap repetitions;
2. leave out each donor and all of that donor's contexts;
3. run 1,000 general and modifier balance repetitions;
4. repeat at the 50-nucleus threshold;
5. rebuild endpoints using PC1 scores;
6. repeat the NCI reference under 50 fold assignments;
7. repeat with nuclear-only TMM normalization factors;
8. perform mtDNA-gene, nuclear-complex, and 82-gene omissions;
9. run range trimming, nonlinear, influence, and QC analyses;
10. save every replicate, failure, and summary; and
11. verify minimum successful repetition counts before applying gates.

**Outputs:**

```text
mitonuclear_stability_replicates.tsv.gz
mitonuclear_general_stability_summary.tsv
mitonuclear_modifier_stability_summary.tsv
mitonuclear_gene_complex_influence.tsv
mitonuclear_qc_normalization_sensitivity.tsv
```

**Ready when:**

Every estimable endpoint row has every applicable mandatory stability field or
an exact `not_testable` reason.

### Task 8: apply endpoint statuses and C3 gates

**Why:**

The final conclusion must be computed from the written rules, not negotiated
after looking at plots.

**Inputs:**

- general and modifier results;
- stability summaries;
- eligibility and compatibility fields; and
- the frozen status precedence and gates.

**Steps:**

1. assign all 168 endpoint-level statuses;
2. apply Gate 2A to all 7 context triplets;
3. apply Gate 2B to all 49 context-by-modifier triplets;
4. classify supported gates as relative imbalance, slope change, both, or
   slope rewiring;
5. calculate residual bridge authorization separately;
6. calculate the primary overall C3 label;
7. calculate secondary-context support without promoting it;
8. join Phase 13 C1 status only after C3 decisions are final;
9. generate exact permitted and prohibited wording; and
10. retain all negative and inconclusive rows.

**Outputs:**

```text
mitonuclear_general_gate_decisions.tsv
mitonuclear_modifier_gate_decisions.tsv
mitonuclear_claim_summary.tsv
```

**Ready when:**

Every gate status and wording field reproduces from named numerical and Boolean
inputs without manual interpretation.

### Task 9: create figure-ready evidence tables

**Why:**

Figures should display the validated evidence rather than recalculate it.

**Inputs:**

- final scores, endpoint results, prediction grids, stability, and gates.

**Steps:**

1. create donor-level mtDNA-versus-nuclear scatter data;
2. add NCI-reference and group-specific fitted lines with confidence bands;
3. create difference/residual forest-plot data with CIs and donor counts;
4. create compact bootstrap and leave-one-donor-out stability data;
5. distinguish `not_testable`, `inconclusive`, `not_supported`, and
   `supported` visually;
6. include context role, family, endpoint, contrast, and gate status; and
7. do not draw causal arrows or final publication figures.

**Outputs:**

```text
mitonuclear_figure_data.tsv.gz
```

**Ready when:**

A later figure script can reproduce every displayed point, line, interval,
count, and label without reopening a model object.

### Task 10: validate and publish atomically

**Why:**

A run is complete only when an independent output-only validator can reproduce
its structure, checks, decisions, and hashes.

**Inputs:**

- every scientific output;
- schemas and expected dimensions; and
- artifact and status contracts.

**Steps:**

1. write all scientific files in a staging directory;
2. write stage and blocking-check tables;
3. write an artifact manifest for every declared file except the artifact
   manifest itself and final status file;
4. write the final status file last inside staging;
5. run an independent output-only validation;
6. require all blocking checks to pass;
7. atomically rename staging to the final directory; and
8. preserve scratch checkpoints separately from the flat final bundle.

**Outputs:**

```text
mitonuclear_stage_status.tsv
mitonuclear_checks.tsv
mitonuclear_artifacts.tsv
mitonuclear_status.tsv
```

**Ready when:**

The published directory is immutable, flat, complete, independently validated,
and contains no undeclared file or subdirectory.

## Output and file contract

Final production root:

```text
results/minerva_production/15_mitonuclear_coupling/
```

| File | Required content |
|---|---|
| `mitonuclear_analysis_manifest.tsv` | One frozen analysis row with approvals, versions, thresholds, models, families, seeds, and hashes |
| `mitonuclear_context_manifest.tsv` | Exactly 7 contexts with order and primary/secondary role |
| `mitonuclear_endpoint_manifest.tsv` | Exactly 3 endpoint definitions, signs, units, SESOIs, and models |
| `mitonuclear_contrast_manifest.tsv` | One general contrast plus exactly 7 inherited modifier definitions and coefficient rules |
| `mitonuclear_module_manifest.tsv` | Exactly 2 inherited respiratory modules and coverage rules |
| `mitonuclear_module_members.tsv` | Exactly 99 inherited module memberships, assay mappings, complex, and admission fields |
| `mitonuclear_input_inventory.tsv` | Required Phase 13 paths, schemas, statuses, bytes, and hashes |
| `mitonuclear_source_checks.tsv` | Upstream identity, count, key, schema, and provenance checks |
| `mitonuclear_donor_eligibility.tsv` | Donor/context/group counts, nuclei, metadata, module coverage, ranges, and 20/50 eligibility |
| `mitonuclear_score_pairs.tsv.gz` | Paired primary and PC1 mtDNA/nuclear scores by donor and context |
| `mitonuclear_crossfit_folds.tsv` | Primary and repeated fold assignments with balancing and held-out checks |
| `mitonuclear_nci_reference_models.tsv` | Six structural model IDs per context (5 cross-fit plus 1 full reference), stored in long form with model metadata, coefficient rows, rank, training-donor IDs/hash, and status |
| `mitonuclear_reference_predictions.tsv.gz` | Donor/context/fold observed, predicted, residual, range, and training provenance |
| `mitonuclear_donor_endpoints.tsv.gz` | Donor-level `D = M - N`, raw and standardized residual values, and paired scores |
| `mitonuclear_general_test_manifest.tsv` | Exactly 21 structural general endpoint rows, family, eligibility, and reason |
| `mitonuclear_modifier_test_manifest.tsv` | Exactly 147 structural modifier endpoint rows, required groups, family, and eligibility |
| `mitonuclear_general_results.tsv` | Exactly 21 estimates, HC3 uncertainty, P/q, effect, direction, and status fields |
| `mitonuclear_modifier_results.tsv` | Exactly 147 direct modifier estimates, HC3 uncertainty, P/q, four group counts, and status fields |
| `mitonuclear_stratum_effects.tsv` | Exactly 126 descriptive endpoint effects/slopes across context and stratum |
| `mitonuclear_group_slopes.tsv` | Fitted slopes, SEs, CIs, Pearson/Spearman correlations, ranges, and group counts |
| `mitonuclear_prediction_grid.tsv.gz` | Fitted general/modifier departures over the frozen shared nuclear-score grid |
| `mitonuclear_model_diagnostics.tsv` | Formula, rank, df, covariance, residual, leverage, linearity, and convergence diagnostics |
| `mitonuclear_score_reliability.tsv` | Coverage, score reconstruction, mean-z/PC1, variance, and range checks |
| `mitonuclear_stability_replicates.tsv.gz` | Long-form bootstrap, LOO, balance, fold, threshold, PC1, normalization, QC, and omission estimates |
| `mitonuclear_general_stability_summary.tsv` | Exactly 21 general endpoint stability summaries |
| `mitonuclear_modifier_stability_summary.tsv` | Exactly 147 modifier endpoint stability summaries |
| `mitonuclear_gene_complex_influence.tsv` | mtDNA leave-one-gene, nuclear leave-one-complex, 82-gene, and matched-complex results |
| `mitonuclear_qc_normalization_sensitivity.tsv` | 50-nucleus, severe-QC, percent-mt diagnostic, nuclear-TMM, range, and nonlinear results |
| `mitonuclear_general_gate_decisions.tsv` | Exactly 7 component-by-component Gate 2A context decisions |
| `mitonuclear_modifier_gate_decisions.tsv` | Exactly 49 component-by-component Gate 2B context-by-contrast decisions |
| `mitonuclear_claim_summary.tsv` | General, sex, APOE, bridge, primary, secondary, C1 handoff, and overall conclusions |
| `mitonuclear_figure_data.tsv.gz` | Plot-ready donor points, fits, intervals, counts, stability, and status labels |
| `mitonuclear_stage_status.tsv` | Stage dependencies, fingerprints, planned/completed/reused/failed shards, and times |
| `mitonuclear_checks.tsv` | Blocking and nonblocking checks with observed and expected values |
| `mitonuclear_artifacts.tsv` | Declared paths, schemas, rows, bytes, SHA-256, and validation states |
| `mitonuclear_status.tsv` | One final technical and scientific status row |

Every TSV begins with `schema_version`. Every inferential result row also
contains, where applicable:

```text
context_id
context_role
scope_id
endpoint_id
contrast_id
family_id
estimate
standard_error
ci_low
ci_high
p_value
q_value
sesoi
effect_meets_sesoi
interval_excludes_zero
interval_inside_sesoi
direction
donor_counts
nuclei_counts
eligibility_status
stability_status
endpoint_status
gate_status
analysis_fingerprint
```

The final directory contains exactly these 36 files, is flat, contains no
scratch subdirectory, and is published atomically.

`mitonuclear_artifacts.tsv` cannot contain its own final hash. It hashes every
declared scientific/control output except itself and `mitonuclear_status.tsv`.
The final status row stores the completed artifact-manifest hash.

## Phase 15 end state

### Scientific and technical end state

Production is technically complete when:

```text
validation_status = validated_complete
contexts = 7
primary_contexts = 3
secondary_contexts = 4
modules = 2
module_memberships = 99
endpoints = 3
modifier_contrasts = 7
general_result_rows = 21
modifier_result_rows = 147
stratum_rows = 126
general_gate_rows = 7
modifier_gate_rows = 49
```

Every structural row has a terminal technical and scientific status. No
positive biological result is required for technical completion.

### Source-controlled files added

| File | Purpose |
|---|---|
| `config/phase15_mitonuclear_coupling.yml` | Frozen contexts, endpoints, models, thresholds, families, stability, paths, schemas, and seeds |
| `scripts/15_run_mitonuclear_coupling.R` | Input validation, score pairing, endpoints, models, stability, gates, and publication |
| `tests/test_phase15_mitonuclear_coupling.R` | Synthetic, unit, integration, leakage, gate, and output-only validation tests |
| `docs/phase_15_mitonuclear_coupling/phase_15_mitonuclear_coupling_plan.md` | This Phase 15 contract |

The existing companion explanation remains in place.

### Existing source-controlled files modified

| File | Required change |
|---|---|
| `scripts/run_pipeline.R` | Register and dispatch the global `mitonuclear_coupling` task after Phase 13 |
| `config/local_pilot.yml` | Add the Phase 15 config path and permit the synthetic pilot task |
| `config/minerva_shared.yml` | Add the Phase 15 config path and permit production execution |

`sandwich`, `edgeR`, and the other required packages are already represented in
`renv.lock`. No lockfile change is planned unless implementation introduces a
new approved sensitivity package.

### Files deleted

None. Phase 15 does not delete or overwrite raw data, Phase 07, Phase 13, Phase
14, or an existing validated Phase 15 bundle. A replacement run uses a new
scratch/staging location and publishes only after independent validation.

### Pipeline registration

```text
task_mode: mitonuclear_coupling
scope: global
stable_task_id: global:mitonuclear_coupling
output_schema: mitochondrial_mitonuclear_coupling_v1
dependency: global:respiratory_modifier
```

Both environment YAML files add:

```yaml
project:
  phase15_mitonuclear_coupling_config: config/phase15_mitonuclear_coupling.yml

scope:
  allowed_task_modes:
    - mitonuclear_coupling
```

The global task rejects `--rds-id`.

The expected dry-run registry row is:

```text
stable_task_id: global:mitonuclear_coupling
scope: global
manifest_row: NA
rds_id: NA
script: scripts/15_run_mitonuclear_coupling.R
output_schema: mitochondrial_mitonuclear_coupling_v1
```

## Local pilot

The local Phase 13 pilot is vasculature-only and cannot exercise the complete
primary C3 design. Phase 15 therefore uses a deterministic synthetic,
Phase-13-compatible fixture with three contexts and repeated donors.

The pilot validates code and contracts only. It must contain:

- a known difference-plus-residual result with no slope change;
- a known slope change;
- a known complete null;
- a precise equivalence result;
- opposite difference/residual signs that must fail compatibility;
- a stable crossing slope labeled `slope_rewiring_observed` that is correctly
  kept outside Gate 2;
- low donor counts producing `provisional_low_power`;
- a rank-deficient reference fold;
- deliberate NCI training leakage that the validator rejects;
- predictor-range mismatch;
- one-donor sign reversal;
- PC1 sign orientation;
- nuclear-only normalization agreement and disagreement examples; and
- known BH and gate-status examples.

Expected pilot dimensions are:

```text
contexts = 3
primary_contexts = 3
secondary_contexts = 0
modules = 2
module_memberships = 99
endpoints = 3
modifier_contrasts = 7
general result rows = 9
modifier result rows = 63
stratum rows = 54
general gate rows = 3
modifier gate rows = 21
validation_status = nonfinal_smoke_test
scientific_decision = not_applicable_pilot
```

Planned commands:

```bash
cd /Users/rzhuang/Documents/VscodeProjects/alzheimer

Rscript tests/test_phase15_mitonuclear_coupling.R

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase mitonuclear_coupling \
  --dry-run

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase mitonuclear_coupling

Rscript tests/test_phase15_mitonuclear_coupling.R \
  --validate-output results/local_pilot/15_mitonuclear_coupling \
  --expected-contexts 3 \
  --expected-general-rows 9 \
  --expected-modifier-rows 63 \
  --expected-stratum-rows 54 \
  --expected-general-gates 3 \
  --expected-modifier-gates 21 \
  --expected-status nonfinal_smoke_test
```

Pilot estimates are synthetic and cannot be used as C3 evidence.

## Minerva production

### Dependency preflight

Before Phase 15 can run:

1. complete and validate production Phase 07 pseudobulk for these nine source
   IDs:

   ```text
   astrocytes
   excitatory_set1
   excitatory_set2
   excitatory_set3
   inhibitory
   immune
   opcs
   oligodendrocytes
   vasculature
   ```

2. run and independently validate Phase 13 production;
3. require Phase 13 status, dimensions, hashes, and blocking checks to pass;
4. approve and freeze the Phase 15 configuration;
5. pass synthetic tests and the local pilot;
6. verify Git, scientific configuration, pipeline configuration, execution
   configuration, and lockfile provenance;
7. cap numeric-library threads at one; and
8. inspect the one-task Phase 15 dry-run graph and analysis fingerprint.

The Phase 07 command template is:

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk \
  --rds-id <one_source_id>
```

Run it separately for the nine listed IDs and validate every resulting status
before running Phase 13. Do not launch Phase 15 merely because a Phase 13
directory exists.

### Phase 15 commands

```bash
cd /sc/arion/work/zhuane01/alzheimer

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

Rscript tests/test_phase15_mitonuclear_coupling.R

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mitonuclear_coupling \
  --dry-run

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mitonuclear_coupling

Rscript tests/test_phase15_mitonuclear_coupling.R \
  --validate-output results/minerva_production/15_mitonuclear_coupling \
  --expected-contexts 7 \
  --expected-primary-contexts 3 \
  --expected-secondary-contexts 4 \
  --expected-general-rows 21 \
  --expected-modifier-rows 147 \
  --expected-stratum-rows 126 \
  --expected-general-gates 7 \
  --expected-modifier-gates 49 \
  --expected-status validated_complete
```

### Checkpointing and resume

Checkpoint long-running work by:

```text
stage
context
endpoint
stability type
replicate shard
```

The resume-compatibility fingerprint includes:

- Phase 13 artifact manifest and required input hashes;
- Phase 15 scientific script and YAML;
- pipeline and execution settings that affect scientific computation;
- frozen module and contrast manifests; and
- `renv.lock`.

Git revision and test-file hashes are recorded as provenance but do not by
themselves invalidate scientifically compatible completed shards. An
incompatible scientific fingerprint starts a new scratch tree.

### Atomic publication order

```text
build and checkpoint in scratch
-> finish every declared scientific stage
-> write scientific files in staging
-> write checks
-> write artifact manifest
-> write final status last inside staging
-> independently validate the complete staging bundle
-> atomically rename staging to the final directory
```

No partial output is published as final. Failed staging directories remain
outside the final root for debugging and are not treated as validated results.

## Required blocking checks

Independent output validation must confirm all of the following.

### Upstream identity and frozen scope

- Phase 13 production status is `validated_complete`;
- every required Phase 13 artifact hash validates;
- exactly 7 contexts, 4 inherited Phase 13 modules, 273 Phase 13 memberships,
  7 modifiers, and 196 Phase 13 result rows are present upstream;
- Phase 15 selects exactly 2 modules and 99 memberships;
- the selected membership symbols, stable IDs, assay features, and respiratory
  complexes match Phase 13 exactly;
- exactly 3 primary and 4 secondary contexts are frozen in the declared order;
- exactly 3 endpoints and 7 modifier contrasts are present; and
- no Phase 08, 10, 11, 12, 14, candidate, fine-cell, or figure artifact appears
  in the Phase 15 scientific input inventory.

### Donors, scores, and references

- donor/context keys are unique;
- `projid` remains character and matches Phase 13 exactly;
- diagnosis, recorded sex, APOE, age, PMI, study, nuclei, and QC fields agree
  across all input joins;
- mtDNA and nuclear score pairs always come from the same donor and context;
- reconstructed Phase 13 scores match stored scores under the frozen tolerance;
- no missing score is imputed;
- module coverage reproduces for both modules in every context;
- all NCI means, SDs, and residual standardizations use only eligible NCI
  donors from the matching context, while `D` is not standardized again;
- every cross-fit fold excludes its held-out NCI donors from training;
- in bootstrap runs, all copies of an original donor occupy one fold and no
  original donor ID occurs in both training and held-out sets;
- every AD prediction uses NCI-trained models only;
- all five training folds are full rank when the residual is declared testable;
- NCI residual means/SDs and every donor prediction reproduce; and
- reference fold assignments reproduce from the frozen seed and IDs.

### Models, contrasts, and multiplicity

- every model uses the frozen formula, coding, and HC3 covariance;
- `study` is included in reference, general, and modifier models;
- the shared saturated slope model includes all 12 group-specific slopes;
- the general slope estimate is the frozen equal-weight average of the six
  stratum AD-minus-NCI slope changes using full model covariance;
- design ranks, residual degrees of freedom, covariance matrices, and
  convergence statuses reproduce;
- the seven difference-of-differences reproduce from hand-audited coefficient
  vectors;
- slope contrasts compare coefficients directly rather than comparing separate
  correlation significance;
- exactly 21 general, 147 modifier, and 126 stratum rows exist;
- all structural untestable rows remain present with exact reasons;
- BH correction reproduces separately for 9, 63, 12, and 84 rows;
- no secondary P value enters a primary family; and
- all SESOI, CI, precise-null, and direction fields reproduce.

### Stability, compatibility, and gates

- whole donors, never nuclei or context rows, are bootstrapped or omitted;
- duplicate bootstrap draws have unique draw IDs and retain original IDs;
- learned normalization, NCI scaling, reference models, and endpoints are
  rebuilt inside resamples while admitted genes remain fixed;
- at least 950 bootstrap and balance repetitions succeed for a supported row;
- supported endpoint rows retain direction in at least 80% of successful
  bootstrap and balanced repetitions;
- no supported endpoint has a leave-one-donor-out sign reversal;
- 50-nucleus, PC1, reference-fold, nuclear-only-normalization, severe-QC, and
  omission checks reproduce;
- percent-mt adjustment is labeled diagnostic, not a hidden primary gate;
- slope predictor-range overlap and common-range trimming reproduce;
- difference/residual signs and slope prediction-grid compatibility reproduce;
- every one of the 168 endpoint statuses follows the frozen precedence;
- exactly 7 general and 49 modifier gate rows exist;
- every Gate 2 Boolean and classification reproduces from saved fields;
- bridge authorization requires both a passing C3 gate and supported residual;
- secondary-only support cannot change the primary overall decision; and
- permitted wording follows the exact endpoint classification and gate.

### Output integrity

- all 36 declared files exist and no undeclared final file or subdirectory
  exists;
- every TSV begins with the expected `schema_version`;
- all expected primary/secondary dimensions match the status row;
- every terminal scientific row has one allowed status;
- no pilot provenance appears in production;
- every declared artifact size, row count, and SHA-256 validates;
- the artifact manifest excludes its own and the final status hash;
- the final status stores the completed artifact-manifest hash; and
- `mitonuclear_status.tsv` was written only after all blocking checks passed.

## Completion criteria

Phase 15 is complete only when:

1. contexts, modules, endpoints, models, contrasts, reference procedure,
   thresholds, FDR families, stability rules, and gates are approved and frozen;
2. the Phase 13 production dependency validates independently;
3. implementation and deterministic synthetic tests pass;
4. the three-context local pilot validates as nonfinal;
5. Minerva production publishes atomically;
6. all 21 general, 147 modifier, and 126 stratum rows are present;
7. all 7 general and 49 modifier gates have terminal statuses;
8. all mandatory stability summaries reproduce;
9. exact permitted wording follows the gates;
10. every input and output has validated provenance; and
11. independent output-only validation passes.

Production completion is:

```text
validation_status = validated_complete
```

regardless of whether C3 is supported, absent, provisional, inconclusive, or
not testable.

## Interpretation and downstream handoff

After the locked Phase 15 review:

1. report the general and modifier C3 decisions separately;
2. report primary and secondary contexts separately;
3. distinguish relative imbalance from a true slope change;
4. name only exact supported contexts and contrasts;
5. preserve e2 low-power labels;
6. join C1, C2, and C3 only as separate claim clauses;
7. authorize the residual bridge only where its exact rule passed;
8. do not begin candidate convergence work for an unauthorized bridge; and
9. retain RNA-expression and same-cohort limitations in every conclusion.

Recommended first figure from the validated bundle:

```text
Panel A: donor mtDNA-versus-nuclear scatter and NCI reference
Panel B: general and modifier endpoint estimates with 95% CIs
Panel C: residual distributions and bridge status
Panel D: bootstrap, leave-one-donor-out, PC1, and normalization stability
```

The figure should show donor counts and mark `not_testable` separately from
`tested_but_unsupported`. It should not use causal arrows.

## Implementation checklist

### Freeze

- [ ] Approve three primary and four secondary contexts.
- [ ] Inherit and verify the 13- and 86-gene modules.
- [ ] Approve all three endpoint definitions and signs.
- [ ] Approve five-fold NCI cross-fitting and repeated-fold rules.
- [ ] Approve general and modifier model formulas, including `study`.
- [ ] Verify all seven contrast vectors with hand examples.
- [ ] Approve the four BH families.
- [ ] Approve endpoint-specific 0.25 SESOIs and interval rules.
- [ ] Approve general, modifier, NCI-reference, and slope eligibility rules.
- [ ] Approve direction compatibility and the rule that
  `slope_rewiring_observed` remains outside Gate 2.
- [ ] Approve bootstrap, LOO, balance, threshold, PC1, normalization, omission,
  QC, range, and nonlinear sensitivities.
- [ ] Approve endpoint status precedence, Gate 2A, Gate 2B, overall labels, and
  bridge authorization.
- [ ] Freeze schemas, seeds, software, paths, and analysis fingerprint inputs.

### Implement

- [ ] Add Phase 15 YAML, script, tests, and pipeline registration.
- [ ] Implement independent Phase 13 status, schema, key, dimension, and hash
  validation.
- [ ] Implement exact reconstruction of both Phase 13 scores.
- [ ] Implement donor/context pairing and eligibility tables.
- [ ] Implement `D = M - N` without a second standardization.
- [ ] Implement leakage-free five-fold NCI references and predictions.
- [ ] Implement general difference, residual, and slope models.
- [ ] Implement modifier difference, residual, and group-slope models.
- [ ] Implement exact HC3 contrasts, CIs, P values, and all four BH families.
- [ ] Implement stratum effects, correlations, score ranges, and prediction
  grids.
- [ ] Implement donor bootstrap and leave-one-donor-out rebuilding.
- [ ] Implement valid general and four-group balanced resampling.
- [ ] Implement 50-nucleus and paired PC1 endpoints.
- [ ] Implement fold, nuclear-only TMM, QC, gene, complex, 82-gene, range,
  nonlinear, and influence sensitivities.
- [ ] Implement endpoint statuses, Gate 2 triplets, classifications, bridge
  authorization, overall decision, and permitted wording.
- [ ] Implement figure-ready tables without plotting inference anew.
- [ ] Implement checkpointing, atomic publication, artifact hashes, and
  output-only validation.

### Validate and execute

- [ ] Pass known-positive, known-null, crossing-slope, leakage, low-count,
  compatibility, range, PC1, normalization, BH, and gate synthetic tests.
- [ ] Validate the three-context local pilot as `nonfinal_smoke_test`.
- [ ] Complete and validate all nine Phase 07 production pseudobulk bundles.
- [ ] Complete and independently validate Phase 13 production.
- [ ] Confirm all Phase 15 definitions remain frozen and no effects were opened.
- [ ] Run Minerva Phase 15 tests and inspect the dry-run registry row.
- [ ] Execute or resume general, modifier, and stability shards.
- [ ] Independently validate all 36 files and structural dimensions.
- [ ] Verify every check, status, gate, and artifact hash.
- [ ] Publish `mitonuclear_status.tsv` last through atomic staging.

### Locked result review

- [ ] Review primary general C3 before secondary contexts.
- [ ] Review modifier C3 separately from general C3.
- [ ] Require two of three endpoints, including residual or slope.
- [ ] Distinguish relative imbalance, slope change, both, and slope rewiring.
- [ ] Label every low-count e2 result as provisional where required.
- [ ] Do not compare significance across contexts as a context-difference test.
- [ ] Set candidate bridge authorization only from exact supported residual rows.
- [ ] Join C1 status only after Phase 15 gates are locked.
- [ ] Use “internally supported in ROSMAP,” not “replicated” or “caused.”
- [ ] Report precise nulls, inconclusive rows, and untestable rows separately.
- [ ] Write the exact allowed conclusion and next-step authorization.
