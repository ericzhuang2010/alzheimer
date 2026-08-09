# Phase 14 Results Explained

## Main purpose

Phase 14 tests **Modifier heterogeneity**: whether the sex- or APOE-dependent
change in an AD-associated respiratory module/program is different across the
seven broad cell contexts.

Phase 13 asks:

> Within each broad cell context, does sex or APOE modify the AD-associated
> module/program effect?

Phase 14 asks:

> Are those Phase 13 modifier effects meaningfully different between broad cell
> contexts?

For example, Phase 14 can determine whether the female-versus-male difference
in the AD-associated nuclear OXPHOS response is larger in astrocytes than in
excitatory neurons.

## The 28 scientific result blocks

The Phase 14 results are organized into:

```text
7 sex/APOE modifiers x 4 respiratory modules/programs = 28 result blocks
```

The seven modifiers are:

1. female versus male within APOE e2 carriers;
2. female versus male within APOE e3/e3;
3. female versus male within APOE e4 carriers;
4. APOE e2 carriers versus APOE e3/e3 within females;
5. APOE e2 carriers versus APOE e3/e3 within males;
6. APOE e4 carriers versus APOE e3/e3 within females; and
7. APOE e4 carriers versus APOE e3/e3 within males.

The four modules/programs are:

1. mtDNA OXPHOS 13;
2. nuclear OXPHOS structural 86;
3. mitochondrial translation 155; and
4. MIB/MICOS 19.

Here, **module** and **program** refer to the same predefined gene set. “Program”
emphasizes the coordinated biological activity represented by the module score.

Each of the 28 result blocks contains three main layers:

1. seven context-specific modifier estimates;
2. one global, or omnibus, heterogeneity test; and
3. 21 direct pairwise context comparisons.

## Result layer 1: 196 context-specific modifier estimates

For every modifier and module/program, Phase 14 estimates the modifier effect
separately in all seven broad cell contexts:

- astrocytes;
- excitatory neurons;
- inhibitory neurons;
- immune cells;
- OPCs;
- oligodendrocytes; and
- vasculature.

The full grid is:

```text
7 contexts x 7 modifiers x 4 modules/programs = 196 estimates
```

These estimates answer questions such as:

> In astrocytes, how much does the AD-associated nuclear OXPHOS effect differ
> between female and male APOE e4 carriers?

They describe the context-specific effects that are compared by the formal
heterogeneity tests. They are not 196 additional Claim 2 hypotheses.

## Result layer 2: 28 global heterogeneity tests

For each modifier-by-module/program result block, Phase 14 performs one omnibus
test across all seven contexts:

```text
7 modifiers x 4 modules/programs = 28 omnibus tests
```

The null hypothesis is:

> The modifier effect is the same in all seven broad cell contexts.

The alternative is:

> At least one broad cell context has a different modifier effect.

A significant omnibus result establishes evidence of context heterogeneity,
but it does not identify which contexts differ. The pairwise results provide
that localization.

The 28 omnibus P values are adjusted together with Benjamini-Hochberg FDR.

## Result layer 3: 588 direct pairwise context tests

Seven contexts form 21 unique unordered pairs:

```text
choose(7, 2) = 21 context pairs
```

For each of the seven modifiers and four modules/programs, Phase 14 compares
the modifier effect between every pair:

```text
21 pairs x 7 modifiers x 4 modules/programs = 588 pairwise tests
```

One pairwise heterogeneity effect is:

```text
H = modifier effect in context A - modifier effect in context B
```

It answers a question such as:

> Is the female-versus-male modifier effect among APOE e4 carriers different
> between astrocytes and excitatory neurons, and by how much?

The output includes the estimated difference, standard error, confidence
interval, P value, FDR-adjusted q value, effect direction, and eligibility and
support status.

All 588 pairwise P values are adjusted as one prespecified family. They are not
adjusted only within omnibus blocks that happen to look promising.

## Result layer 4: 168 descriptive stratum effects

Phase 14 also reports the AD-minus-NCI module/program effect for each of the six
sex/APOE strata within each context:

```text
7 contexts x 6 sex/APOE strata x 4 modules/programs = 168 effects
```

The six strata are:

- female APOE e2 carrier;
- male APOE e2 carrier;
- female APOE e3/e3;
- male APOE e3/e3;
- female APOE e4 carrier; and
- male APOE e4 carrier.

These results make the modifier estimates interpretable. For example, they can
show whether a female-versus-male contrast is caused by a positive AD effect in
females, a negative AD effect in males, or both. They are descriptive support,
not another confirmatory Claim 2 test family.

## Comparable module/program scores

Phase 14 must compare like with like. A module/program may not have exactly the
same usable genes in every cell context, so simply comparing the original Phase
13 scores could confuse gene-coverage differences with biological differences.

For each module/program, Phase 14 therefore constructs a common score using the
genes that pass the prespecified admission rule in all seven contexts. The
scores are recalculated and standardized using NCI reference data within each
context.

The result bundle reports:

- which genes entered each common score;
- which genes were excluded and why;
- the donor-level common scores;
- the NCI reference parameters; and
- agreement with PC1 and original Phase 13 scores.

These are measurement and provenance results supporting the heterogeneity
tests, rather than separate biological claims.

## Donor-overlap and testability results

The same ROSMAP donor can contribute more than one cell context. Phase 14 uses
that repeated-donor structure rather than treating context samples as
independent.

The output reports:

- donor counts in each context and sex/APOE group;
- donors shared by each pair of contexts;
- whether the context-overlap graph supports the global test;
- whether each omnibus and pairwise row is estimable; and
- the exact reason for every untestable row.

This distinguishes “no heterogeneity was found” from “the available data could
not test heterogeneity reliably.”

## Stability and sensitivity results

A small P value alone is not enough for a supported Claim 2 result. Phase 14
also evaluates whether the conclusion survives:

- donor bootstrap resampling;
- leave-one-donor-out analysis;
- pair-complete analysis;
- a minimum 50-nuclei threshold;
- balanced group resampling;
- PC1 scoring;
- original Phase 13 scoring; and
- prespecified QC and model sensitivities.

The output contains both the replicate-level results and summaries for the 28
omnibus and 588 pairwise rows.

## Pairwise decision results

Every one of the 588 pairwise rows receives one terminal status:

| Status | Interpretation |
|---|---|
| `supported` | The complete statistical, effect-size, sample-size, Phase 13 consistency, and stability gate passes |
| `provisional_low_power` | All non-count rules pass, but a required paired group has only 5-9 donors |
| `statistically_detectable_but_small` | The statistical criteria pass, but the effect is smaller than the prespecified meaningful difference |
| `not_supported_precise_null` | The confidence interval is entirely inside the negligible-effect range |
| `inconclusive` | The evidence cannot distinguish meaningful heterogeneity from no heterogeneity |
| `not_testable` | Coverage, donor count, model, covariance, or another required input prevents estimation |

For a pair to be called `supported`, the parent omnibus q value and pairwise q
value must both pass, the absolute context difference must be at least 0.25 NCI
score standard-deviation units, its confidence interval must exclude zero, the
donor and stability rules must pass, and the result must be compatible with the
corresponding Phase 13 evidence.

## Global and overall decision results

Each of the 28 modifier-by-module/program result blocks receives a global
status:

| Status | Interpretation |
|---|---|
| `supported_and_localized` | The omnibus test passes and at least one context pair is supported |
| `global_only` | The omnibus test passes, but no named pair passes the complete localization gate |
| `provisional` | Heterogeneity is present, but only low-power pairs carry it |
| `not_supported_precise_null` | Pairwise intervals support negligible differences and the omnibus test does not pass |
| `inconclusive` | Available evidence cannot resolve the question |
| `not_testable` | The global comparison cannot be estimated |

The phase then combines the sex, APOE, direct-respiratory, and supporting-program
evidence into one overall scientific decision:

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

Only supported results from mtDNA OXPHOS 13 or nuclear OXPHOS structural 86 can
produce the headline `supported_both`, `supported_sex_only`, or
`supported_apoe_only` decisions. Mitochondrial translation and MIB/MICOS are
supporting programs.

## Worked example

Suppose Phase 14 examines the female-versus-male modifier within APOE e4
carriers for the nuclear OXPHOS structural program.

An illustrative result could be:

```text
global seven-context omnibus q = 0.01
astrocyte modifier effect = -0.80
excitatory-neuron modifier effect = -0.15
astrocyte-minus-excitatory-neuron H = -0.65
95% CI excludes 0
pairwise q <= 0.05
all sample-size and stability gates pass
```

This would support the statement that the sex modification of the
AD-associated nuclear OXPHOS response differs between astrocytes and excitatory
neurons. The negative pairwise value means that the female-versus-male modifier
effect is 0.65 standardized score units lower in astrocytes than in excitatory
neurons, under the contrast orientation defined above.

If the omnibus q value passed but no individual pair passed the complete gate,
the result would be `global_only`: heterogeneity across the seven contexts would
be detected, but it could not be assigned confidently to a particular pair.

## Result-count summary

| Result type | Count | Role |
|---|---:|---|
| Context-specific modifier estimates | 196 | Show the modifier effect in each context |
| Global omnibus tests | 28 | Test whether a modifier varies anywhere across contexts |
| Direct pairwise tests | 588 | Identify which pairs of contexts differ |
| Within-stratum AD effects | 168 | Explain the underlying sex/APOE-specific AD effects |
| Global decisions | 28 | Summarize each modifier-by-program result block |
| Pairwise decisions | 588 | Record whether each localized comparison is supported |
| Overall phase decision | 1 | Summarize Claim 2 across sex, APOE, and program roles |

The 28 omnibus tests and 588 pairwise tests are the formal Claim 2 test
families. The 196 context estimates and 168 stratum effects explain those tests
but are not additional Claim 2 hypotheses.

## What Phase 14 does not establish

Phase 14 can establish that modifier effects differ among the seven broad cell
contexts and can localize those differences to named context pairs. It does not
by itself establish:

- heterogeneity among the 54 fine cell types;
- a causal biological mechanism;
- protein-level respiratory dysfunction;
- mitochondrial flux or functional impairment; or
- replication in an independent cohort.

Those conclusions require separate analyses or validation data.

