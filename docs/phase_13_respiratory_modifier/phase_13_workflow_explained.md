# phase 13 workflow

## A beginner explanation and methodological justification

## Short answer

This phase13/C1 analysis is different from the existing Zhang–Yu similarity score.

The similarity score starts with earlier gene-level differential-expression
calls. It changes each result into `+1`, `0`, or `−1` and summarizes how often
two groups agree across cell types.

The C1 analysis goes back to the donor-level RNA counts. It asks directly:

> Is the Alzheimer-disease-versus-NCI expression difference larger, smaller, or
> reversed in one sex or APOE group compared with another?

The proposed workflow is:

```text
Raw nucleus-level counts
          ↓
Add nuclei within the same donor and cell type
          ↓
One all-gene profile per donor and cell type
          ↓
Normalize the all-gene profiles
          ↓
Calculate four module scores for every donor
          ↓
Keep donors as separate biological samples
          ↓
Estimate AD − NCI within each sex/APOE group
          ↓
Directly compare the AD effects between groups
          ↓
Check individual genes, whole gene sets, uncertainty, and stability
```

Many parts of this workflow are established research practice. The complete
workflow is not a universal recipe, however. The four selected modules, the
exact NCI-reference scoring formula, the minimum sample-size rules, and the
stability gate are project-specific decisions.

## 1. How this differs from the similarity score

| Feature | Existing Zhang–Yu similarity score | New C1 analysis |
|---|---|---|
| Starting information | Previous DEG calls | Raw RNA counts |
| Basic unit | One gene | One donor and one module |
| Gene value | `+1`, `0`, or `−1` | Continuous normalized expression |
| Uses the size of the change? | No | Yes |
| Combines cell types? | Yes, when calculating one gene's score | No; first tests each cell context separately |
| Main question | Do two groups show similar thresholded DEG patterns? | Is the AD effect actually different between groups? |
| Formal sex/APOE interaction? | No | Yes |

The similarity score changes every available gene result into:

```text
+1 = significantly increased in AD
 0 = not statistically significant
−1 = significantly decreased in AD
```

It then asks how often two groups agree across available cell types. It does not
use the exact expression measurements or exact sizes of the AD effects.

The C1 analysis instead uses continuous donor-level measurements and directly
tests the difference between two AD effects.

The existing method is documented in the
[Phase 10 similarity explanation](../phase_10_similarity/similarity_calculation_cross_celltypes_explained.md).

## 2. What “one expression profile per donor and cell type” means

The expression profile must contain all usable genes, not only the genes in the
four mitochondrial modules.

Suppose one donor has 500 eligible astrocyte nuclei. For every gene, add the raw
RNA counts from those 500 nuclei:

```text
Donor 1001 + astrocytes
    NDUFA1 total count
    NDUFA2 total count
    APOE total count
    TUFM total count
    ...
    all other measured genes
```

This produces:

```text
one donor × one cell type × all genes
```

### Small example

Suppose Donor 1001 has three astrocyte nuclei:

| Gene | Nucleus 1 | Nucleus 2 | Nucleus 3 | Donor total |
|---|---:|---:|---:|---:|
| `NDUFA1` | 2 | 1 | 3 | 6 |
| `TUFM` | 4 | 2 | 3 | 9 |
| `APOE` | 8 | 5 | 7 | 20 |
| Gene X | 1 | 0 | 2 | 3 |

The donor's astrocyte profile is:

```text
NDUFA1 = 6
TUFM   = 9
APOE   = 20
Gene X = 3
...
```

The same operation is repeated for every eligible donor and cell type.

### Why retain all genes?

All genes are needed to:

- correct for differences in sequencing depth;
- correct for differences in RNA-library composition;
- remove genes with too little information;
- supply a fair background for pathway testing;
- run gene-level direct interaction tests; and
- compare mitochondrial modules with suitable non-mitochondrial genes.

The correct order is:

```text
Build complete donor profiles using all genes
                       ↓
Normalize the complete profiles
                       ↓
Extract and score the four frozen modules
```

Do not construct the donor profiles using only the four mitochondrial sets.

## 3. How to calculate a module score for every donor

A module score summarizes the expression of many genes with a related
biological job into one number.

Each eligible donor receives four scores in each eligible cell context:

1. mtDNA-encoded OXPHOS;
2. nuclear-encoded OXPHOS;
3. mitochondrial translation; and
4. MIB/MICOS and inner-membrane organization.

The complete proposed gene lists are in
[`c1_respiratory_module_gene_lists.md`](c1_respiratory_module_gene_lists.md).

### Step 3A: Normalize the complete donor profiles

Some donors have more total RNA reads than others. Raw counts therefore cannot
be compared directly.

Normalization adjusts for differences in:

- total sequencing depth; and
- RNA-library composition.

The planned procedure uses TMM normalization followed by log counts per million,
or logCPM.

The practical meaning is:

> After normalization, expression measurements from different donors are on a
> comparable scale.

### Step 3B: Establish an NCI reference for each gene

Within one cell context, use eligible NCI donors to estimate:

- the average expression of each gene; and
- how much that gene varies among the NCI donors.

For example:

| Gene | NCI average | NCI standard deviation |
|---|---:|---:|
| `NDUFA1` | 5.0 | 0.5 |
| `NDUFA2` | 6.0 | 1.0 |
| `NDUFS1` | 4.0 | 0.4 |

A standard deviation describes how spread out donor values are around their
average.

The reference is calculated separately for each cell context because a gene
can naturally have different expression levels in astrocytes and neurons.

“NCI reference” does not mean biologically normal or pathology-free. It means
only the expression reference estimated from the NCI comparison donors.

### Step 3C: Put each gene on a comparable scale

For each donor and gene, calculate:

```text
standardized gene value =
    (donor expression − NCI average)
    ÷ NCI standard deviation
```

This standardized value is commonly called a z score.

Its interpretation is:

```text
 z =  0   donor is at the NCI reference average
 z = +1   donor is one NCI standard deviation above the reference average
 z = −1   donor is one NCI standard deviation below the reference average
```

Standardization is important because genes naturally have very different
expression levels. Without it, a few highly expressed genes could dominate the
module score.

### Step 3D: Average the standardized genes in the module

Suppose a simplified module contains three genes and one donor has:

| Gene | Standardized value |
|---|---:|
| Gene A | +1.0 |
| Gene B | +0.5 |
| Gene C | −0.2 |

The donor's module score is:

```text
(+1.0 + 0.5 − 0.2) ÷ 3 = +0.43
```

This donor's module expression is moderately above the NCI reference.

In the real analysis, the score averages the measured and eligible genes from
the frozen module. The analysis must report which genes entered every score.

### Example output table

| Donor | Cell type | Diagnosis | Sex | APOE | mtDNA score | Nuclear OXPHOS score | Translation score | Membrane score |
|---|---|---|---|---|---:|---:|---:|---:|
| 1001 | Astrocyte | NCI | Female | ε4 | 0.10 | 0.05 | −0.04 | 0.12 |
| 1002 | Astrocyte | AD | Female | ε4 | −0.70 | −0.55 | −0.31 | −0.20 |
| 1003 | Astrocyte | AD | Male | ε4 | −0.15 | −0.08 | 0.02 | 0.03 |

Every donor remains a separate row.

## 4. How donors are combined statistically

There are two very different meanings of “combine” in this workflow.

### Correct: combine nuclei within one donor

```text
500 astrocyte nuclei from Donor 1001
                  ↓
one astrocyte profile for Donor 1001
```

The nuclei came from the same person, so they do not represent 500 independent
people.

### Incorrect: merge different donors into one profile

Do not do this:

```text
All female ε4 donors
        ↓
one combined female ε4 RNA profile
```

That would remove the donor-to-donor variation needed to estimate uncertainty.

Instead, keep the donors separate:

```text
Female ε4 NCI:
    Donor 1001 score
    Donor 1005 score
    Donor 1012 score
    ...

Female ε4 AD:
    Donor 1020 score
    Donor 1031 score
    Donor 1048 score
    ...
```

### How the group effect is estimated

Consider this made-up example:

| Group | Individual donor module scores | Unadjusted group average |
|---|---|---:|
| Female ε4 NCI | 0.1, −0.1, 0.0 | 0.0 |
| Female ε4 AD | −0.5, −0.7, −0.6 | −0.6 |
| Female ε3/ε3 NCI | 0.1, 0.0, −0.1 | 0.0 |
| Female ε3/ε3 AD | −0.1, −0.2, 0.0 | −0.1 |

First calculate the female ε4 AD effect:

```text
−0.6 − 0.0 = −0.6
```

Then calculate the female ε3/ε3 AD effect:

```text
−0.1 − 0.0 = −0.1
```

Then directly compare the two effects:

```text
−0.6 − (−0.1) = −0.5
```

The final `−0.5` is the C1 APOE-modifier estimate in this example.

The real model keeps all donors separate, adjusts for age and postmortem
interval, and calculates uncertainty around the difference.

### Combination summary

| Operation | Do it? |
|---|---|
| Add nuclei from the same donor and cell type | Yes |
| Combine standardized genes into one module score for one donor | Yes |
| Merge different donors into one RNA profile | No |
| Use all individual donors to estimate group effects and uncertainty | Yes |

## 5. Why this workflow makes biological and statistical sense

### Reason 1: the biological question concerns people, not isolated nuclei

Diagnosis, sex, APOE genotype, age, and postmortem interval are donor-level
properties. Thousands of nuclei from one donor do not create thousands of
independent people.

Treating every nucleus as independent can make the sample size appear much
larger than it truly is and underestimate normal differences between people.

Summing counts within donor and cell type preserves cell-type information while
making the donor the biological replicate.

### Reason 2: summing raw counts preserves count information

Adding raw counts within a donor and cell type creates data that can be analyzed
with established replicated RNA-count methods.

It also gives donors with more observed RNA better measurement precision
without pretending that their nuclei are independent people.

### Reason 3: keeping all genes permits valid normalization and comparison

Sequencing depth and RNA composition differ between donors. Normalizing only a
small selected set could make the answer depend on the genes chosen in advance.

Keeping the full usable transcriptome gives the normalization and pathway test
a stable reference.

### Reason 4: modules match the biological question

OXPHOS is performed by many genes acting together. One gene can change by chance,
and many genuinely coordinated genes can each have changes too small to pass an
individual DEG threshold.

A donor module score asks whether the system moves together. Gene-level results
remain important for showing which genes contribute.

### Reason 5: standardizing before averaging prevents one gene from dominating

mtDNA genes can have much higher RNA counts than many nuclear genes.

If raw or unstandardized expression values were simply added, a few abundant
genes could determine the score. Gene-wise standardization gives each gene a
comparable scale before averaging.

### Reason 6: the direct comparison answers C1

C1 asks whether the AD effect differs by sex or APOE. Therefore, the analysis
must test the difference between two AD effects.

Finding a significant AD result in one group and a nonsignificant result in
another does not establish that the groups differ. The difference itself must
be tested.

### Reason 7: individual donor values provide honest uncertainty

Keeping donors separate shows:

- how much people differ from one another;
- whether one donor is creating the result;
- how wide the confidence interval is; and
- whether small APOE groups provide enough information.

### Reason 8: stability checks test whether the conclusion is fragile

Bootstrap resampling, leaving out one donor, applying a stricter nucleus
threshold, and using an alternative module score ask whether the same conclusion
survives reasonable changes.

A result that disappears whenever one donor is removed should not become a
headline conclusion.

## 6. Is this a standard procedure used by other researchers?

### Established or widely supported parts

#### Treating the donor as the biological replicate

Yes. This is a strongly supported approach for multi-donor single-cell and
single-nucleus differential-expression analysis.

Pseudobulk benchmarking studies have shown that ignoring biological replicates
can produce false discoveries. They aggregate raw counts for the same cell type
within each biological sample and then apply replicated-count methods.

Relevant primary studies include:

- [Crowell et al., 2020, `muscat detects subpopulation-specific state transitions`](https://www.nature.com/articles/s41467-020-19894-4)
- [Squair et al., 2021, `Confronting false discoveries in single-cell differential expression`](https://www.nature.com/articles/s41467-021-25960-2)
- [Zimmerman et al., 2021, `A practical solution to pseudoreplication bias in single-cell studies`](https://www.nature.com/articles/s41467-021-21038-1)
- [Benchmarking differential states in multi-subject single-cell data](https://pmc.ncbi.nlm.nih.gov/articles/PMC9487674/)

These papers do not say that pseudobulk is the only valid method. Proper
mixed-effects models can also account for repeated cells within donors.
Pseudobulk is attractive here because it is understandable, auditable, and
well matched to the existing raw-count data.

#### Summing raw counts within donor and cell type

Yes. Summing raw counts is a commonly used pseudobulk construction. Benchmarks
have generally found that summing counts and then applying bulk-RNA count
normalization performs better than first normalizing single cells and then
averaging them.

#### Using replicated-count models

Yes. Packages such as edgeR were designed to analyze replicated RNA count data
while accounting for biological variation:

- [Robinson, McCarthy, and Smyth, 2010, `edgeR`](https://pubmed.ncbi.nlm.nih.gov/19910308/)

#### Testing an interaction directly

Yes. Directly testing whether two effects differ is standard statistical
practice.

The general error of treating “significant in one group” and “not significant
in another group” as proof that groups differ is explained by:

- [Gelman and Stern, 2006, `The Difference Between “Significant” and “Not Significant” Is Not Itself Statistically Significant`](https://doi.org/10.1198/000313006X152649)

#### Testing predefined gene sets

Yes. Researchers commonly test whether predefined groups of biologically
related genes move together.

The planned `camera` analysis accounts for correlation among genes in the same
set:

- [Wu and Smyth, 2012, `Camera: a competitive gene set test accounting for inter-gene correlation`](https://pmc.ncbi.nlm.nih.gov/articles/PMC3458527/)

### Common concept, but no single universal formula

#### Module scores

Summarizing a gene set with one score per sample is common. There is no single
universally accepted scoring formula.

Researchers use several approaches, including:

- average standardized expression;
- principal components;
- GSVA-like sample scores;
- rank-based scores; and
- direct gene-set models without a separate score.

The proposed NCI-reference z-score average is a transparent project-specific
choice. It is easy to explain because:

- zero means the NCI reference average;
- positive values mean higher expression than that reference;
- negative values mean lower expression.

Because the exact formula is not universal, C1 should also be checked with:

- an NCI-trained first principal component score; and
- a correlation-aware gene-set test such as `camera`.

Agreement among these approaches is stronger evidence than dependence on one
chosen score.

### Project-specific choices

The following are not universal standards:

- the exact four mitochondrial modules;
- using the strict 86-gene nuclear OXPHOS definition;
- the custom 19-gene membrane-organization module;
- the exact NCI-reference scoring rule;
- the ≥20- and ≥50-nucleus thresholds;
- the planned minimum donor numbers;
- the 80% bootstrap-direction rule;
- the exact smallest meaningful effect;
- the selected primary cell classes; and
- the exact multiple-testing families.

These choices can still be scientifically sound. They must be:

1. biologically justified;
2. written down before looking at the confirmatory C1 results;
3. reported clearly; and
4. checked with reasonable alternatives.

### Good practice that is stricter than many published workflows

The following checks are not always included in published studies, but they
make this project more credible:

- leave-one-donor-out analysis;
- donor bootstrap;
- stricter nucleus-count sensitivity;
- alternative module scoring;
- matched non-mitochondrial gene-set comparisons;
- complete module coverage reporting; and
- independent replication.

They do not guarantee that the conclusion is true, but they reveal fragile or
analysis-dependent results.

## 7. What should be considered the main C1 evidence?

The most defensible C1 package contains three connected levels.

### Level 1: direct gene-level effects

Fit the donor-level model using the complete usable transcriptome. Save the
direct sex and APOE modifier estimate for every gene.

Then show the results for genes in the four frozen modules.

### Level 2: donor module-score effects

Calculate one module score per donor and cell context. Directly test whether the
AD effect on that score differs by sex or APOE.

This gives an understandable effect size and confidence interval.

### Level 3: correlation-aware gene-set result

Use the complete ranked gene results to ask whether genes in the module move
together more strongly than the rest of the tested transcriptome.

This prevents the conclusion from depending entirely on a particular module
score formula.

### Required stability

Any proposed headline effect must also survive the prespecified donor and
quality-control sensitivity checks.

The logic is:

```text
direct modifier effect
        +
coherent module result
        +
compatible gene-set result
        +
donor/QC stability
        =
internal support for C1
```

## 8. What this workflow can and cannot establish

If the tests pass, the study can support wording such as:

> In astrocytes, the AD-associated nuclear OXPHOS expression difference was
> modified by APOE group.

It cannot establish from RNA data alone that:

- mitochondrial respiration itself increased or decreased;
- ATP production changed;
- sex or APOE caused the expression change;
- one candidate network gene regulated the module; or
- the effect is specific to one cell type unless C2 also passes.

Functional respiration measurements, perturbation experiments, and independent
replication answer those stronger questions.

## 9. Recommended implementation rule

Use this workflow as the working C1 design, but label its pieces accurately:

| Workflow component | Classification |
|---|---|
| Donor as biological replicate | Established best-supported practice |
| Sum raw counts within donor and cell type | Standard pseudobulk approach |
| Normalize all genes and use a replicated-count model | Standard RNA-count analysis |
| Direct AD-by-sex/APOE interaction | Standard statistical requirement |
| Test predefined gene sets | Standard pathway-analysis idea |
| NCI-reference average z score | Transparent project-specific module score |
| Four selected modules | Project-specific biological hypothesis |
| Exact thresholds and gate rules | Project-specific confirmation rules |
| Bootstrap, leave-one-out, alternate score, and QC checks | Strong robustness practice |

The project should therefore say:

> We use a donor-level pseudobulk and direct-interaction framework supported by
> multi-sample single-cell differential-expression research. We apply a
> prespecified, project-specific mitochondrial module definition and validate
> it with alternative scoring, correlation-aware gene-set testing, and donor
> sensitivity analyses.
