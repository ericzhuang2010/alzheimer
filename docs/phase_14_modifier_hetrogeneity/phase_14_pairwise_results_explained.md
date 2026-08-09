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

## 2. Where the 588 pairwise tests come from

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

## 3. How to interpret the sign

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

## 4. Example 1: opposite sex patterns across cell contexts

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

## 5. Example 2: similar effects in both contexts

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

## 6. Example 3: negative APOE pairwise result

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

## 7. Example 4: “significant here, not significant there” is insufficient

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

## 8. What one pairwise result row contains

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

## 9. What is the parent omnibus result?

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

## 10. When can a pair be called supported?

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

## 11. Why paired donor counts matter

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

## 12. Possible final statuses

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

## 13. Direct respiratory modules versus supporting modules

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

## 14. A simple reading order for one pairwise result

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

## 15. Main point to remember

A Phase 14 pairwise result does not ask:

> Is nuclear OXPHOS expression higher in astrocytes than in excitatory
> neurons?

It asks:

> Is the sex/APOE modification of the AD-versus-NCI nuclear OXPHOS expression
> effect different between astrocytes and excitatory neurons?

That direct difference is what allows Phase 14 to support careful wording such
as “the modifier differed between these broad cell contexts.”
