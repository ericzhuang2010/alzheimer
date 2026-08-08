# Why Phase 13 uses broad rather than fine cell types

Phase 13 does not avoid fine cell types merely because there are 54 of them.
The larger problem is that many fine types do not contain enough eligible
donors and nuclei for reliable sex/APOE interaction tests.

## Problems with an all-fine-type primary analysis

### Low donor counts

Each direct modifier contrast requires four diagnosis-by-group combinations.
Some fine types have fewer than five donors in at least one required group,
making the contrast not testable. Groups with 5-9 donors permit estimation but
remain provisional and cannot pass the internal-confirmation rule.

### Low RNA counts

Fine cell types contain fewer nuclei per donor. This produces noisier donor
pseudobulk profiles and less reliable module/program scores.

### Large multiple-testing burden

An all-54-fine-type primary grid would contain:

```text
54 fine cell types
x 7 direct sex/APOE contrasts
x 4 frozen modules/programs
= 1,512 scientific hypotheses
```

Phase 13 would then produce 1,512 primary module/program-score P values and
1,512 supporting `camera` P values. This is substantially larger than the
seven-broad-context design:

```text
7 broad cell contexts
x 7 direct sex/APOE contrasts
x 4 frozen modules/programs
= 196 scientific hypotheses
```

### Unstable estimates

Small fine-type groups are more vulnerable to a single influential donor,
unequal group sizes, and failure during bootstrap or leave-one-donor-out
analysis.

### Incomplete donor overlap

Different fine types can contain different subsets of donors. This makes
comparisons less precise and can make an apparent fine-type difference reflect
different donor availability rather than biology.

### Confirmatory versus exploratory purpose

Phase 13 is a prespecified donor-level confirmation analysis. An unrestricted
54-fine-type screen would be closer to an exploratory cell-atlas analysis and
would require its own manifests, power rules, multiple-testing families, and
claim language.

## Why broad aggregation helps

For each donor, Phase 13 adds counts from related fine types before applying the
broad-context nucleus threshold:

```text
related fine types from one donor
        |
        v
one broad donor profile
        |
        v
more nuclei and more eligible donors
        |
        v
more stable module/program score
```

Different donors are never combined. The independent biological sample remains
one donor in one broad cell context.

## Tradeoff

Broad aggregation can hide fine-subtype heterogeneity. Opposing effects in two
fine types can partially cancel, and a broad result does not prove that every
fine subtype behaves identically.

The planned analysis hierarchy is therefore:

1. Test all seven broad contexts in Phase 13.
2. Lock the broad-context results.
3. Run selected fine-type localization analyses only for prespecified,
   adequately powered fine types.
4. Do not let a significant fine-type result rescue a failed broad-context
   primary test.

In summary, the reason is not simply that 54 fine cell types are too many. An
all-fine-type primary analysis would combine severe multiple testing with many
low-power, noisy, and unstable comparisons. Broad contexts provide the more
reliable confirmatory analysis, while selected fine types remain useful for
localizing supported broad-context findings.
