# Phase 13: AD mean, Delta, gene values, and module scores explained

## Short answer

Yes, Phase 13 calculates an expression value for each usable gene in each
donor. However, the primary Claim 1 test does not simply count differentially
expressed genes. It combines the genes in each planned mitochondrial module
into one module score for every donor and then compares those donor scores.

There are three calculation levels:

| Level | What Phase 13 calculates |
|---|---|
| Gene level | A normalized expression value for each gene in each donor and cell context |
| Donor level | One score for each mitochondrial module in each donor and cell context |
| Group level | A model-adjusted average of donor scores for an exact AD or NCI sex-by-APOE group |

The formal Phase 13 analysis is described in the
[main analysis plan](phase_13_respiratory_modifier_plan.md). A related guide
explains the [module-score formulas](phase_13_module_score_clarification.md).

## 1. Start with one expression profile per donor and cell context

The donor, not an individual nucleus, is the independent biological sample.

For each donor and broad cell context, Phase 13 adds the raw RNA counts from
all eligible nuclei belonging to that donor and context. This is sometimes
called a **pseudobulk profile**.

For example:

```text
Donor A, excitatory neurons:
    MT-ND1 raw count
    MT-ND2 raw count
    MT-CO1 raw count
    TUFM raw count
    ...
    every other measured gene
```

Phase 13 does this using all measured genes. It does not first keep only the
four mitochondrial modules. All-gene data are needed to perform filtering and
normalization correctly.

Most importantly, Phase 13 never combines all AD nuclei into one giant AD
sample. Each donor remains a separate sample.

## 2. Calculate a normalized value for every usable gene

Donors can have different numbers of RNA reads. Raw counts therefore cannot
be compared directly. Phase 13 adjusts the donor libraries for sequencing
depth and composition and obtains a normalized `logCPM` value for every usable
gene in every donor.

At this point, one donor has one number for each gene:

```text
Donor A, excitatory neurons:
    normalized MT-ND1 expression = one number
    normalized MT-ND2 expression = one number
    normalized MT-CO1 expression = one number
    ...
```

The complete normalized expression data support two related analyses:

1. individual-gene models, which ask how one gene changes; and
2. module-score models, which ask whether a planned group of related genes
   changes together.

## 3. Put genes in a module onto a comparable scale

Genes naturally have very different expression levels. A highly expressed
gene should not dominate a module simply because its RNA is abundant.

For each admitted module gene, Phase 13 uses the eligible NCI donors in the
same cell context as a reference. NCI means the comparison group labeled
**no cognitive impairment**; it does not mean pathology-free or biologically
normal.

For donor `d`, gene `g`, and cell context `c`:

```text
standardized gene value
    = (donor's normalized expression - NCI average for that gene)
      / variation among NCI donors for that gene
```

The formal notation is:

```text
z(d,g,c) =
    [logCPM(d,g,c) - mean_NCI(g,c)]
    / sd_NCI(g,c)
```

Interpretation:

- `z = 0`: expression is at the NCI reference average;
- `z = +1`: expression is one NCI standard deviation above that average; and
- `z = -1`: expression is one NCI standard deviation below that average.

This calculation is performed separately for every admitted gene.

## 4. Make one module score for every donor

Phase 13 then averages the standardized gene values belonging to one frozen
module. Every admitted gene receives equal weight.

For example, suppose an illustration uses three module genes:

```text
Donor A standardized gene values:

    MT-ND1 = +0.8
    MT-ND2 = +0.4
    MT-CO1 = +0.6

raw donor module score
    = (+0.8 + 0.4 + 0.6) / 3
    = +0.6
```

The real mtDNA OXPHOS module contains 13 frozen genes, subject to its planned
measurement and coverage rules. The same procedure is used for each of the
four planned modules.

Phase 13 then scales the donor module scores one more time using their NCI
donor distribution:

```text
standardized donor module score
    = (raw donor module score - NCI module-score average)
      / NCI module-score standard deviation
```

On this final scale:

- the pooled NCI module-score average is approximately `0`; and
- one score unit is one NCI donor-level module-score standard deviation in
  that cell context.

Each donor therefore has one score for each tested module and cell context.

```text
Donor A, excitatory neurons:
    mtDNA OXPHOS score
    nuclear OXPHOS score
    mitochondrial-translation score
    MIB/MICOS inner-membrane score
```

## 5. What does "AD mean" mean?

Take one exact group, such as female APOE e2 AD donors in excitatory neurons.
Each donor in that group has a separate module score:

```text
Female e2 AD donors:
    Donor A = +0.5
    Donor B = +0.8
    Donor C = +0.2
```

The simple arithmetic average in this small illustration is:

```text
(+0.5 + 0.8 + 0.2) / 3 = +0.5
```

However, the official Phase 13 **AD mean** is not merely this raw average. It
is the group average estimated by the statistical model after accounting for:

- age at death;
- postmortem interval, or PMI; and
- ROS versus MAP parent study.

It is therefore better described as the **model-adjusted AD group mean**.
Phase 13 estimates a corresponding model-adjusted NCI group mean.

The mean is calculated across donor scores. It is not calculated by treating
individual nuclei as independent samples.

## 6. What is Delta?

The Greek letter Delta, written `Delta` or `Δ`, means a difference or change.
In Phase 13, within one sex, APOE group, and cell context:

```text
Delta
    = model-adjusted AD mean
      - model-adjusted NCI mean
```

For example:

```text
Female e2, excitatory neurons:

    adjusted AD module-score mean  = +0.50
    adjusted NCI module-score mean =  0.00

    Delta(Female,e2)
        = +0.50 - 0.00
        = +0.50
```

This example means that the module score is estimated to be `0.50` score units
higher in female e2 AD donors than in female e2 NCI donors, after the planned
adjustments.

The cell context is left out of the short notation, but it is always present
in the actual analysis. More completely, the notation would be:

```text
Delta(Female, e2, excitatory neurons)
```

## 7. How Phase 13 compares female and male AD effects

Phase 13 does not prove a sex difference by saying that females were
significant and males were not. It directly compares the two Deltas:

```text
Delta(Female,e2) - Delta(Male,e2)
```

Expanded, this is:

```text
(AD Female e2 - NCI Female e2)
    -
(AD Male e2 - NCI Male e2)
```

This is called a **difference-of-differences**.

For example:

```text
Delta(Female,e2) = +0.60
Delta(Male,e2)   = -0.20

female-minus-male modifier
    = +0.60 - (-0.20)
    = +0.80
```

The positive result means that the AD-associated module change is `0.80`
score units more positive, or less negative, in female e2 donors than in male
e2 donors in that cell context.

It does not mean that females have `0.80` more DEGs.

## 8. Are individual genes also tested?

Yes. Phase 13 also fits a separate count-based model for every adequately
measured gene. Each gene can receive:

- an AD-versus-NCI effect;
- a direct sex or APOE modifier effect;
- an uncertainty estimate and 95% confidence interval;
- a P value; and
- a multiple-testing-adjusted q value.

A gene may be called a **differentially expressed gene**, or DEG, if it meets
the declared gene-level statistical and effect-size rules. `Delta` itself is
not a DEG:

```text
Delta = a numerical AD-versus-NCI effect
DEG   = a gene classification based on an effect and statistical evidence
```

The gene-level results help show which module members contribute to a module
pattern. They are supporting evidence rather than the primary Claim 1 test.

## 9. The complete calculation in one picture

```text
Raw RNA counts from all eligible nuclei
                  |
                  v
Add counts within each donor and cell context
                  |
                  v
One all-gene expression profile per donor and context
                  |
                  v
Normalize every usable gene across donor samples
                  |
                  +-------------------------------+
                  |                               |
                  v                               v
       Individual-gene models          Standardize module genes
       supporting evidence             using the NCI reference
                                                  |
                                                  v
                               Average module genes for each donor
                                                  |
                                                  v
                                  One module score per donor
                                                  |
                                                  v
                             Estimate adjusted AD and NCI means
                                                  |
                                                  v
                              Delta = AD mean - NCI mean
                                                  |
                                                  v
                   Compare Deltas directly across sex or APOE groups
```

## 10. Main point to remember

Phase 13 does not establish Claim 1 by counting DEGs. Its primary question is:

> Does the combined donor-level mitochondrial module score show a different
> AD-versus-NCI effect across the planned sex or APOE groups?

Individual genes explain the pattern. Donor module scores provide the primary
Claim 1 test.
