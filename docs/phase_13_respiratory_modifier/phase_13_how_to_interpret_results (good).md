# Phase 13: how to understand the 196 planned test results

## Short answer

Phase 13 produces **196 result rows**, not merely 196 unexplained numbers.
Each row represents one planned scientific test and contains:

- one primary effect estimate;
- a 95% confidence interval;
- a P value and multiple-testing-adjusted q value;
- the donor counts in the four required groups;
- stability and quality-control results; and
- one final scientific status.

The primary estimate asks:

> In one cell context and for one mitochondrial module, how different is the
> AD-versus-NCI expression effect between two planned sex or APOE groups?

For background on how donor module scores and `Delta` are calculated, see
[Phase 13: AD mean, Delta, gene values, and module scores explained](<phase_13_score_explained (good).md>).
The complete formal rules are in the
[Phase 13 respiratory modifier plan](phase_13_respiratory_modifier_plan.md).

## 1. Where the 196 tests come from

Every result row is one combination of:

```text
one of 7 broad cell contexts
×
one of 7 direct sex/APOE comparisons
×
one of 4 mitochondrial modules
```

Therefore:

```text
7 contexts × 7 comparisons × 4 modules = 196 planned tests
```

### Seven broad cell contexts

1. Astrocytes
2. Excitatory neurons
3. Inhibitory neurons
4. Immune cells
5. Oligodendrocyte precursor cells, or OPCs
6. Oligodendrocytes
7. Vasculature cells

### Four mitochondrial modules

1. The 13 mtDNA-encoded OXPHOS genes
2. The 86 nuclear-encoded structural OXPHOS genes
3. The 155 mitochondrial-translation genes
4. The 19 MIB/MICOS and inner-membrane-organization genes

### Seven direct comparisons

The three sex comparisons are:

```text
Female − Male within e2
Female − Male within e33
Female − Male within e4
```

The four APOE comparisons are:

```text
e2 − e33 within females
e4 − e33 within females
e2 − e33 within males
e4 − e33 within males
```

Here, `e33` means APOE ε3/ε3.

## 2. How one result row is constructed

For each cell-context-by-module combination, Phase 13 first estimates six
AD-versus-NCI effects:

```text
Delta(Female,e2)
Delta(Female,e33)
Delta(Female,e4)
Delta(Male,e2)
Delta(Male,e33)
Delta(Male,e4)
```

Each `Delta` is:

```text
model-adjusted AD module-score mean
    −
model-adjusted NCI module-score mean
```

Phase 13 then compares two of those Deltas directly:

```text
primary estimate = Delta(group 1) − Delta(group 2)
```

This is a **difference-of-differences**. It is not a comparison of whether one
group had a significant P value and another group did not.

There are:

```text
7 contexts × 4 modules × 6 Deltas = 168 descriptive stratum effects
```

Those 168 values help explain the 196 direct tests, but they are not 168
additional primary hypotheses.

## 3. What the primary estimate means

The main number in one result row is the signed `estimate`.

Because the donor module scores are standardized, the estimate is measured in
**NCI donor-level module-score standard deviations** for that cell context.

The estimate is not:

- a number of differentially expressed genes;
- an individual-gene fold change;
- a percentage;
- an absolute expression level; or
- exactly Cohen's d.

### Worked example: female e4 versus female e33

Suppose a result row is:

```text
Cell context: excitatory neurons
Module: nuclear OXPHOS
Comparison: female e4 − female e33
```

Suppose the adjusted AD effects are:

```text
Delta(Female,e4)  = −0.50
Delta(Female,e33) = +0.10
```

The primary estimate is:

```text
estimate
    = Delta(Female,e4) − Delta(Female,e33)
    = −0.50 − (+0.10)
    = −0.60
```

Plain-language interpretation:

> In excitatory neurons, the AD-associated nuclear OXPHOS expression change
> is estimated to be 0.60 module-score standard deviations more negative in
> female e4 donors than in female e33 donors.

This does **not** mean that female e4 AD donors have an absolute module score
of `−0.60`. It describes how their AD-versus-NCI difference compares with the
female e33 AD-versus-NCI difference.

## 4. How to interpret positive and negative estimates

The sign must always be interpreted using the subtraction order recorded in
the row's `contrast_id`.

### Sex comparison

For:

```text
Delta(Female,e2) − Delta(Male,e2)
```

- a positive estimate means the AD effect is more positive, or less negative,
  in females;
- a negative estimate means the AD effect is more negative, or less positive,
  in females.

### APOE comparison

For:

```text
Delta(Female,e4) − Delta(Female,e33)
```

- a positive estimate means the female e4 AD effect is more positive than the
  female e33 AD effect;
- a negative estimate means the female e4 AD effect is more negative than the
  female e33 AD effect.

### “More positive” does not necessarily mean “increased in both groups”

For example:

```text
Delta(Female,e4)  = −0.10
Delta(Female,e33) = −0.70

estimate = −0.10 − (−0.70) = +0.60
```

Both AD effects are negative. The estimate is positive because the e4 AD
effect is **less negative** than the e33 AD effect.

## 5. Do not interpret the estimate alone

Every result row should be read using all of these fields:

| Field | Question it answers |
|---|---|
| `context_id` | In which broad cell context was the test performed? |
| `module_id` | Which mitochondrial module was tested? |
| `contrast_id` | Which two AD effects were compared, and in which order? |
| `estimate` | What are the estimated direction and size of the difference? |
| `ci_lower`, `ci_upper` | How uncertain is that estimate? |
| P value | What is the evidence before correcting for all planned tests? |
| q value | What is the evidence after correcting the complete 196-test family? |
| Four donor counts | Did all four required diagnosis-by-group cells have enough donors? |
| Module coverage | Were enough frozen module genes measured and usable? |
| `camera` result | Did a separate gene-set method point in a compatible direction? |
| Stability fields | Did the direction survive donor resampling, donor removal, and sensitivity analyses? |
| Final status | What conclusion is scientifically permitted? |

## 6. Example of a complete result row

Imagine the following output:

```text
Context: excitatory neurons
Module: nuclear OXPHOS
Contrast: female e4 − female e33

Estimate: −0.60
95% CI: [−0.90, −0.30]
q value: 0.01
Minimum required-group size: 11 donors
Bootstrap repetitions with the same sign: 94%
Leave-one-donor-out sign reversals: 0
Final status: supported
```

This row says:

1. the estimated modifier is negative;
2. its point estimate is reasonably large under the project's rule;
3. the confidence interval does not include zero;
4. it survives the multiple-testing correction;
5. all four required groups have at least 10 donors;
6. most donor bootstraps preserve the direction;
7. removing any one donor does not reverse the direction; and
8. every other mandatory support rule also passed.

Only after checking all of those conditions may the row be called
`supported`.

## 7. Understanding the confidence interval

The 95% confidence interval describes uncertainty around the estimate.

### Precise negative estimate

```text
estimate = −0.60
95% CI = [−0.90, −0.30]
```

The entire interval is below zero. This is compatible with a negative
modifier.

### Large-looking but uncertain estimate

```text
estimate = −0.60
95% CI = [−1.40, +0.20]
```

The point estimate looks large, but the interval is wide and crosses zero.
The data are compatible with a strong negative effect, a small effect, or
even a positive effect. This row cannot be called supported.

### Why a nonsignificant result is not automatically “no effect”

A row with a q value above `0.05` may simply be too imprecise. To conclude
that a meaningful effect is not supported precisely, the interval must be
narrow enough to fall completely inside the project's small-effect range.

## 8. Understanding the 0.25 project threshold

Phase 13 defines `0.25` module-score standard deviations as the smallest
meaningful **point estimate** for the primary gate:

```text
absolute estimate ≥ 0.25
```

Examples:

```text
estimate = +0.60  → point estimate exceeds the threshold
estimate = +0.10  → point estimate is below the threshold
estimate = −0.40  → absolute point estimate exceeds the threshold
```

This threshold is a project rule chosen before examining the Phase 13 results.
It is not a universal law of mitochondrial biology. The q value, confidence
interval, donor count, and stability requirements must also pass.

The rule does not prove that the true effect is larger than `0.25`; it says
that the point estimate meets the planned meaningful-size rule while the
confidence interval excludes zero.

## 9. Understanding the P value and q value

The P value evaluates one test before accounting for all the other planned
tests. Because Phase 13 asks 196 related questions, it separately adjusts the
196 primary module-score P values using the Benjamini-Hochberg procedure.

The resulting q value answers a more appropriate question:

> How strong is this row's statistical evidence after accounting for the
> complete planned family of module-score tests?

The primary support rule requires:

```text
q ≤ 0.05
```

A small q value is necessary but not sufficient. A row can have a small q
value and still be too small, underpowered, unstable, or technically
unreliable.

## 10. Understanding the final row status

Every planned row receives exactly one final status.

| Status | Plain-language interpretation |
|---|---|
| `supported` | The effect, q value, donor counts, module coverage, uncertainty, and every mandatory stability rule passed |
| `provisional_low_power` | All non-count support rules passed, but at least one required group had only 5–9 donors |
| `statistically_detectable_but_small` | The q and nonzero-interval rules passed, but the absolute estimate was smaller than 0.25 |
| `not_supported_precise_null` | The complete confidence interval was inside the range from −0.25 to +0.25 |
| `inconclusive` | The interval, stability evidence, or a mandatory sensitivity was too uncertain to support either a meaningful effect or a precise null |
| `not_testable` | Donor count, module coverage, design rank, or missing required data made the model impossible to estimate |

The labels are applied in a fixed order so that one attractive number cannot
override a major weakness.

## 11. What `supported` requires

A row is `supported` only when every planned requirement passes, including:

1. at least 10 eligible donors in each of the four required groups;
2. sufficient usable genes from the frozen module;
3. primary module-score q value at most `0.05`;
4. absolute estimate at least `0.25` and a 95% interval excluding zero;
5. a compatible direction from the separate `camera` gene-set analysis;
6. at least 80% of donor bootstraps retaining the direction;
7. no leave-one-donor-out sign reversal;
8. acceptable agreement between the primary score and the alternative PC1
   score;
9. compatible results at the 50-nucleus threshold and in balanced resamples;
10. no single gene, respiratory complex, or translation category controlling
    the conclusion; and
11. stability after the frozen severe-QC exclusion.

This is why reading only `estimate` and `q` is insufficient.

## 12. The same hypothesis has several linked result files

Phase 13 saves several 196-row tables. They do not represent separate sets of
196 independent discoveries. They provide different evidence about the same
196 planned hypotheses.

| File | Role |
|---|---|
| `respiratory_module_results.tsv` | Primary donor module-score estimate, interval, P value, and q value |
| `respiratory_camera_results.tsv` | Supporting correlation-aware gene-set result |
| `respiratory_stability_summary.tsv` | Bootstrap, leave-one-donor-out, balance, threshold, QC, and omission evidence |
| `respiratory_gate_decisions.tsv` | Component-by-component decision and final status for each row |

The safest file for the final interpretation is
`respiratory_gate_decisions.tsv`, while the other tables explain why each row
received that decision.

## 13. Direct respiratory modules versus supporting modules

Only these two modules can directly support the main C1 respiratory/OXPHOS
wording:

```text
mtdna_oxphos_13
nuclear_oxphos_structural_86
```

The other modules support narrower conclusions:

```text
mitochondrial_translation_155
    → mitochondrial-translation expression

mib_micos_inner_membrane_19
    → mitochondrial inner-membrane organization
```

A supported translation or MIB/MICOS row cannot be relabeled as a supported
OXPHOS row.

The modules also should not be treated as four fully independent
confirmations. They use overlapping donors, and some modules share genes.

## 14. A simple reading order for every row

Use this order whenever examining one of the 196 tests:

1. **Can it be tested?** Check donor eligibility, gene coverage, and model
   status.
2. **What exactly was compared?** Read the context, module, and subtraction
   order in the contrast.
3. **What were the two component AD effects?** Read the two Deltas that create
   the difference-of-differences.
4. **Which direction does the estimate show?** Interpret the sign using the
   subtraction order.
5. **How large is it?** Compare the absolute point estimate with `0.25`.
6. **How uncertain is it?** Read the 95% confidence interval.
7. **Did it survive multiple-testing correction?** Read the q value.
8. **Is it donor-stable?** Check bootstrap and leave-one-donor-out results.
9. **Do alternative calculations agree?** Check PC1, 50-nucleus, balance,
   `camera`, QC, and omission results.
10. **What is the final permitted conclusion?** Use the frozen row status and
    permitted wording.

## 15. Main point to remember

Do not ask only:

> Is the estimate positive or negative?

Instead ask:

> In this cell context, for this mitochondrial module, was the AD-versus-NCI
> effect different between these two sex/APOE groups—and was that difference
> large enough, precise enough, statistically corrected, adequately powered,
> and stable enough to trust?

That complete question is what each Phase 13 result row is designed to answer.
