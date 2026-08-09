# Phase 14: pairwise cell-context results explained

## Short answer

A Phase 14 pairwise result compares two broad cell contexts. It asks:

> Is the Phase 13 sex/APOE modifier stronger, weaker, or reversed in one cell
> context compared with another?

It does **not** simply compare gene expression between two cell types.

The full formal analysis is specified in the
[Phase 14 modifier heterogeneity plan](phase_14_modifier_heterogeneity_plan.md).
The [general Phase 14 results guide](phase_14_results_explained.md) provides
additional background.

## 1. Phase 13 versus Phase 14

Phase 13 calculates a modifier separately in each cell context:

```text
Phase 13 modifier
    = [AD − NCI in group 1]
      −
      [AD − NCI in group 2]
```

Phase 14 compares two Phase 13-style modifiers:

```text
Phase 14 pairwise result
    = Phase 13 modifier in context 1
      −
      Phase 13 modifier in context 2
```

The Phase 14 value is called `H`, for heterogeneity:

```text
H = M(context 1) − M(context 2)
```

Here:

- `M` is the sex/APOE modifier estimated in one cell context; and
- `H` is the difference between the two cell-context modifier estimates.

Phase 14 is therefore a difference between two
**difference-of-differences**.

## 2. Does Phase 14 simply subtract saved Phase 13 values?

### The conceptual answer is yes

The scientific quantity is a subtraction:

```text
H = modifier in context 1 − modifier in context 2
```

For example, suppose Phase 13 reports:

```text
astrocyte modifier         = +0.40
excitatory-neuron modifier = −0.50
```

The intuitive Phase 14 difference is:

```text
H = +0.40 − (−0.50) = +0.90
```

This arithmetic explains the meaning of `H`.

### The computational answer is no

Phase 14 must not copy two displayed Phase 13 numbers into a spreadsheet and
subtract them. It uses the validated Phase 13 data and definitions, rebuilds
comparable scores, and estimates the pairwise difference inside a joint
statistical model.

There are three main reasons.

### Reason 1: Phase 13 scores may use different genes in different contexts

Phase 13 determines usable genes separately in each context. For example, a
nuclear OXPHOS score might use:

```text
astrocytes:          80 usable genes
excitatory neurons:  74 usable genes
```

Those two Phase 13 scores represent slightly different measured gene sets. A
strict context comparison should compare the same program definition.

Before viewing the Phase 14 heterogeneity results, Phase 14 finds the module
genes that are usable in all seven contexts. It then rebuilds each context's
donor scores using that common gene set.

### Reason 2: the same donors can appear in multiple contexts

One person may contribute both an astrocyte profile and an excitatory-neuron
profile. These are not observations from two unrelated people:

```text
astrocyte profile from Donor A
excitatory-neuron profile from Donor A
```

Phase 14 fits a joint mixed-effects model with a donor random intercept. This
tells the model that several context profiles can belong to the same person.

### Reason 3: the shared uncertainty, or covariance, matters

The pairwise point estimate is:

```text
H = M1 − M2
```

Its variance is:

```text
Var(H)
    = Var(M1)
      + Var(M2)
      − 2 × Cov(M1,M2)
```

`Cov(M1,M2)` describes how the two estimates move together, partly because
many of the same donors contribute to both contexts.

Therefore, Phase 14 must not calculate uncertainty as:

```text
SE(H) = sqrt[SE(M1)^2 + SE(M2)^2]
```

That shortcut assumes the two estimates are independent and ignores the
shared-donor information. Phase 14 instead obtains the covariance and the
correct confidence interval directly from the joint model.

### What Phase 14 actually does

Phase 14 performs the following workflow:

1. Read and validate the Phase 13 counts, donor information, modules, context
   definitions, contrast definitions, and result statuses.
2. Find a common usable gene set for each module across all seven contexts.
3. Recalculate comparable donor module scores using those common genes.
4. Stack the context profiles into one repeated-donor dataset.
5. Fit one joint mixed-effects model for each of the four modules.
6. Estimate the inherited Phase 13-style modifier in every context from that
   joint model.
7. Subtract each frozen context pair within the joint model.
8. Calculate the standard error, confidence interval, and P value using the
   exact model covariance.
9. Correct all 588 pairwise tests as one prespecified family.
10. Run paired-donor, bootstrap, leave-one-donor-out, alternative-score, and
    quality-control checks.

Thus, Phase 14 fits four primary joint module models. It derives all 588
pairwise comparisons from those models; it does not fit 588 unrelated models.

### Why the Phase 14 numbers may differ slightly from Phase 13

Suppose Phase 13 reports:

```text
astrocytes:          +0.40
excitatory neurons:  −0.50
simple difference:   +0.90
```

After using common genes and the joint repeated-donor model, Phase 14 might
estimate:

```text
astrocytes:          +0.37
excitatory neurons:  −0.46
Phase 14 H:           +0.83
95% CI:              [+0.30, +1.36]
```

This small difference is not automatically an error. The Phase 14 values come
from the deliberately more comparable score and joint model. Phase 14 still
checks whether the rebuilt context effects are directionally compatible with
the carried Phase 13 result.

### What is inherited and what is recalculated?

| Inherited from Phase 13 | Recalculated in Phase 14 |
|---|---|
| Donor-level counts and metadata | Common-gene module scores |
| Seven broad context definitions | Joint-model context modifier estimates |
| Seven modifier definitions and subtraction signs | Pairwise `H` estimates |
| Four frozen module definitions | Exact standard errors and confidence intervals |
| Donor eligibility and quality information | Omnibus and pairwise P/q values |
| Phase 13 row statuses | Phase 14 stability evidence and final statuses |

Phase 14 does not subtract:

- P values;
- q values;
- DEG counts; or
- significance labels.

It subtracts model-estimated sex/APOE modifier effects.

The best summary is:

> Phase 14 is mathematically based on subtracting pairs of Phase 13-style
> modifier effects, but it rebuilds comparable scores and estimates those
> differences in a joint repeated-donor model rather than merely subtracting
> the saved Phase 13 table values.

## 3. Where the 588 pairwise tests come from

Seven broad cell contexts produce 21 unique context pairs:

```text
choose 2 contexts from 7 = 21 pairs
```

For each pair, Phase 14 tests every inherited sex/APOE modifier and
mitochondrial module:

```text
21 context pairs
× 7 sex/APOE modifiers
× 4 mitochondrial modules
= 588 pairwise tests
```

Each result row therefore represents:

```text
one cell-context pair
+ one sex/APOE modifier
+ one mitochondrial module
```

The seven contexts are:

1. Astrocytes
2. Excitatory neurons
3. Inhibitory neurons
4. Immune cells
5. Oligodendrocyte precursor cells, or OPCs
6. Oligodendrocytes
7. Vasculature cells

## 4. How to interpret the sign

The context order is frozen before testing:

```text
H = context 1 modifier − context 2 modifier
```

| H value | Meaning |
|---|---|
| Positive | The Phase 13 modifier is more positive, or less negative, in context 1 |
| Negative | The modifier is more negative, or less positive, in context 1 |
| Near zero | The modifier is similar in the two contexts |

The meaning of “more positive” still depends on the inherited Phase 13
contrast.

### Female-minus-male contrast

For:

```text
Delta(Female,e4) − Delta(Male,e4)
```

a positive modifier means the AD effect is more positive, or less negative,
in females than males.

### e4-minus-e33 contrast

For:

```text
Delta(Female,e4) − Delta(Female,e33)
```

a positive modifier means the female e4 AD effect is more positive, or less
negative, than the female e33 AD effect.

## 5. Example 1: opposite sex patterns across cell contexts

Consider this planned row:

```text
Context pair:
    astrocytes − excitatory neurons

Module:
    nuclear OXPHOS

Modifier:
    Female − Male within e4
```

### Astrocytes

Suppose:

```text
Delta(Female,e4) = +0.10
Delta(Male,e4)   = −0.30

astrocyte modifier
    = +0.10 − (−0.30)
    = +0.40
```

In astrocytes, the AD-related OXPHOS effect is more positive in females than
males.

### Excitatory neurons

Suppose:

```text
Delta(Female,e4) = −0.40
Delta(Male,e4)   = +0.10

excitatory-neuron modifier
    = −0.40 − (+0.10)
    = −0.50
```

In excitatory neurons, the AD-related OXPHOS effect is more negative in
females than males.

### Phase 14 pairwise result

```text
H
    = astrocyte modifier − excitatory-neuron modifier
    = +0.40 − (−0.50)
    = +0.90
```

Plain-language interpretation:

> The female-versus-male modification of the AD-associated nuclear OXPHOS
> expression effect is estimated to be 0.90 standardized module-score units
> more positive in astrocytes than in excitatory neurons.

This is a strong-looking cell-context difference because the sex pattern
reverses direction. It still needs a confidence interval, q value, adequate
paired donor counts, and all stability checks before it can be called
supported.

## 6. Example 2: similar effects in both contexts

Suppose:

```text
astrocyte modifier         = +0.40
excitatory-neuron modifier = +0.35

H = +0.40 − (+0.35) = +0.05
```

Interpretation:

> The sex modifier is almost the same in astrocytes and excitatory neurons.

Both Phase 13 context modifiers could be biologically supported while the
Phase 14 pairwise difference is approximately zero. This would suggest that
the modifier may be shared across the two contexts rather than different
between them.

## 7. Example 3: negative APOE pairwise result

Consider:

```text
Context pair:
    excitatory neurons − inhibitory neurons

Module:
    nuclear OXPHOS

Modifier:
    Female e4 − Female e33
```

Suppose:

```text
excitatory-neuron modifier = −0.70
inhibitory-neuron modifier = +0.10

H = −0.70 − (+0.10) = −0.80
```

Interpretation:

> The female e4-versus-e33 modification of the AD-associated nuclear OXPHOS
> effect is estimated to be 0.80 standardized score units more negative in
> excitatory neurons than in inhibitory neurons.

The negative sign does not mean that OXPHOS expression is generally lower in
excitatory neurons. It refers specifically to the e4-versus-e33 difference in
the AD effect.

## 8. Example 4: “significant here, not significant there” is insufficient

Suppose the Phase 13-style context results are:

```text
Astrocytes:
    modifier = +0.45
    q = 0.03

Excitatory neurons:
    modifier = +0.35
    q = 0.20
```

It may be tempting to call the modifier astrocyte-specific because only the
astrocyte result is significant. That conclusion would be incorrect.

The direct Phase 14 comparison is:

```text
H = +0.45 − (+0.35) = +0.10
```

If the confidence interval for `H` crosses zero, Phase 14 finds no convincing
difference between the contexts. The different Phase 13 q values could result
from different donor counts or uncertainty rather than genuinely different
biological effects.

This is why Phase 14 tests the difference directly.

## 9. What one pairwise result row contains

Each of the 588 rows should include:

| Field | Meaning |
|---|---|
| `context_1`, `context_2` | The two cell contexts and their subtraction order |
| `contrast_id` | The inherited Phase 13 sex/APOE comparison |
| `module_id` | The mitochondrial program being compared |
| Context 1 modifier | Phase 13-style modifier estimated in the first context |
| Context 2 modifier | Phase 13-style modifier estimated in the second context |
| `H` estimate | Context 1 modifier minus context 2 modifier |
| 95% confidence interval | Uncertainty around `H` |
| Pairwise P value | Evidence before correcting the complete pairwise family |
| Pairwise q value | Evidence after correction across all 588 pairwise tests |
| Parent omnibus q value | Whether the modifier differs somewhere among all seven contexts |
| Paired donor counts | Donors represented in both contexts for each required group |
| Stability results | Bootstrap, donor-removal, pair-complete, alternative-score, and QC agreement |
| Final status | The conclusion permitted for this cell-context pair |

The primary estimate is reported in standardized module-score units. Phase 14
uses the same admitted genes across all seven contexts for a module before
testing context differences, which makes the program definitions comparable.

## 10. What is the parent omnibus result?

For each of the seven modifiers and four modules, Phase 14 first asks whether
the modifier differs anywhere among the seven contexts:

```text
7 modifiers × 4 modules = 28 omnibus tests
```

The omnibus test does not say which pair differs. The 588 pairwise tests
localize a passing global difference to named context pairs.

The strict Phase 14 gate requires the relevant parent omnibus q value to pass
before a named pair can be called supported. If the omnibus passes but no
individual pair passes its complete gate, the correct conclusion is:

> The modifier differs somewhere among the seven analyzed contexts, but the
> study did not reliably localize that difference to one named pair.

## 11. When can a pair be called supported?

A Phase 14 pair is supported only when all major requirements pass:

1. The parent seven-context omnibus q value is at most `0.05`.
2. The pairwise q value is at most `0.05` after correction across all 588
   pairwise tests.
3. The absolute `H` estimate is at least `0.25` standardized score units.
4. The 95% confidence interval excludes zero.
5. At least one matching Phase 13 context row is supported for the same
   modifier and module.
6. Every one of the four required groups has at least 10 donors represented in
   both contexts.
7. Bootstrap, leave-one-donor-out, pair-complete, PC1, QC, and model
   sensitivity checks pass.
8. The module is described according to its direct-respiratory or supporting
   biological role.

A large `H` estimate by itself is therefore insufficient.

## 12. Why paired donor counts matter

Many donors contribute profiles for more than one cell context. Phase 14 uses
a repeated-donor model so those profiles are not treated as observations from
different people.

For a named pair, Phase 14 also counts donors who are represented in both
contexts within each of the four required diagnosis-by-group cells:

- fewer than 5 paired donors in any required group makes the pair not
  testable;
- 5–9 paired donors allows only a provisional result; and
- at least 10 paired donors in all four groups is required for an internally
  supported pairwise claim.

The word “pairwise” refers to a pair of cell contexts. “Paired donors” refers
to donors measured in both of those contexts. These are related but different
ideas.

## 13. Possible final statuses

| Status | Interpretation |
|---|---|
| `supported` | Convincing evidence that the modifier differs between the two named contexts |
| `provisional_low_power` | The other rules passed, but at least one paired group has only 5–9 donors |
| `statistically_detectable_but_small` | The difference is statistically detectable but its absolute estimate is smaller than 0.25 |
| `not_supported_precise_null` | The complete confidence interval is inside the range from −0.25 to +0.25 |
| `inconclusive` | The estimate, interval, or stability evidence is too uncertain |
| `not_testable` | Paired donor count, gene coverage, model rank, covariance, or another required input prevents estimation |

A q value above `0.05` is not automatically a precise null. A wide confidence
interval means the result may simply be inconclusive.

## 14. Direct respiratory modules versus supporting modules

Only pairwise results for these two modules can directly support headline
wording about respiratory-modifier heterogeneity:

```text
mtdna_oxphos_13
nuclear_oxphos_structural_86
```

The other modules support narrower wording:

```text
mitochondrial_translation_155
    → mitochondrial-translation modifier heterogeneity

mib_micos_inner_membrane_19
    → inner-membrane-organization modifier heterogeneity
```

Translation-only or membrane-only results cannot be renamed as OXPHOS
heterogeneity.

## 15. A simple reading order for one pairwise result

When examining one Phase 14 pairwise row, use this order:

1. **What is being compared?** Read the module, modifier, context 1, and
   context 2.
2. **What are the two context modifiers?** Understand the Phase 13-style
   effect in each context.
3. **What is the subtraction order?** Confirm that `H = context 1 − context 2`.
4. **What does the sign mean?** Determine which context has the more positive
   modifier.
5. **How large is the difference?** Compare `|H|` with `0.25`.
6. **How uncertain is it?** Read the 95% confidence interval.
7. **Did it survive correction?** Read both the pairwise and parent omnibus q
   values.
8. **Were enough paired donors available?** Check all four group counts.
9. **Is it stable?** Check bootstrap, donor-removal, pair-complete, PC1, QC,
   and model sensitivity results.
10. **What wording is allowed?** Use the frozen final status rather than visual
    judgment.

## 16. Main point to remember

A Phase 14 pairwise result does not ask:

> Is nuclear OXPHOS expression higher in astrocytes than in excitatory
> neurons?

It asks:

> Is the sex/APOE modification of the AD-versus-NCI nuclear OXPHOS expression
> effect different between astrocytes and excitatory neurons?

That direct difference is what allows Phase 14 to support careful wording such
as “the modifier differed between these broad cell contexts.”
