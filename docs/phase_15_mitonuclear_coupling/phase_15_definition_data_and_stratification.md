# Claim C3: Definition, Data Requirements, and Analysis Stratification

## 1. What exactly is C3?

C3 is a claim about coordination between the mitochondrial and nuclear genomes at the RNA-expression level:

> Does Alzheimer disease alter the normal relationship between expression of mtDNA-encoded respiratory-chain genes and expression of nuclear-encoded OXPHOS structural-subunit genes?

It is not simply “mitochondrial genes are differentially expressed in AD.”

### Biological meaning

OXPHOS protein complexes contain subunits encoded in two places:

- mtDNA encodes 13 respiratory-chain proteins.
- Nuclear DNA encodes most of the remaining OXPHOS structural subunits.

These two sets normally need coordinated expression. C3 asks whether that coordination is altered in AD.

For example, suppose an NCI donor's nuclear OXPHOS score predicts an mtDNA score of `0.7`, but an AD donor with the same nuclear score has an observed mtDNA score of `0.2`:

```text
mitonuclear residual = observed mtDNA - predicted mtDNA
                     = 0.2 - 0.7
                     = -0.5
```

The negative residual means that mtDNA expression is lower than expected from the normal NCI relationship.

Several outcomes are possible:

| Observation | Does it necessarily support C3? |
|---|---|
| Nuclear OXPHOS decreases, but mtDNA changes proportionally | No; coordination may be preserved. |
| mtDNA decreases, but nuclear OXPHOS changes proportionally | Not necessarily. |
| mtDNA becomes lower than expected from nuclear OXPHOS | Potentially yes. |
| The correlation or slope between the two scores weakens or changes in AD | Potentially yes. |

Thus, C3 is specifically about a change in the relationship between the two compartments, not merely a change in one compartment. See [Task 4 in the main plan](../mitochondrial_deep_dive_next_steps_plan.md#task-4-test-the-mtdna-nuclear-relationship).

## 2. Data needed

### 2.1 Raw donor-level RNA counts

The plan uses existing ROSMAP single-nucleus RNA-seq raw UMI counts. Counts must be aggregated into one pseudobulk profile for every donor and cell context:

```text
donor x cell context x gene
```

The primary broad contexts are:

- astrocytes;
- excitatory neurons;
- inhibitory neurons.

Individual nuclei cannot be treated as independent samples because multiple nuclei come from the same person. The donor must be the statistical unit.

For each profile, the plan requires:

- raw gene counts;
- donor ID;
- cell-type identity;
- number of nuclei;
- total UMI and detected genes;
- mitochondrial-read fraction;
- QC flags.

The current rule is at least 20 nuclei for a primary donor-cell profile and at least 50 for a sensitivity analysis. See [Task 1 in the main plan](../mitochondrial_deep_dive_next_steps_plan.md#task-1-build-one-expression-profile-per-donor-and-cell-context).

### 2.2 Donor biological and technical metadata

For every donor, C3 needs:

- diagnosis: AD or NCI;
- sex;
- APOE genotype/group;
- age at death;
- postmortem interval (PMI);
- donor ID linking profiles across cell types;
- planned RNA-quality measurements.

Diagnosis is necessary for the AD-versus-NCI question. Sex and APOE are needed both as adjustments in the NCI reference and for modifier-specific versions of C3.

### 2.3 Two frozen gene sets

Before examining the new results, the analysis must define:

1. **mtDNA respiratory score**

   Expression of the frozen 13 mtDNA-encoded respiratory-chain genes.

2. **Nuclear OXPHOS score**

   Expression of nuclear-encoded OXPHOS structural-subunit genes, with all mtDNA genes excluded.

The nuclear list should remain focused on structural subunits. Assembly factors and broadly mitochondrial genes should not be silently added after seeing the results.

### 2.4 NCI donors

NCI donors are essential because they define the reference relationship.

Within each cell context, NCI donors provide:

- the reference mean and standard deviation for each score;
- the expected relationship between nuclear OXPHOS and mtDNA expression;
- the model used to calculate how far each donor deviates from that relationship.

The reference should be fitted separately within each broad cell context. Cross-fitting or leave-one-out prediction prevents an NCI donor from helping construct its own expected value.

## 3. The three required C3 measurements

The plan requires all three analyses. It does not permit choosing whichever gives the smallest P value.

### 3.1 Endpoint 1: Standardized difference

First standardize both scores using the NCI distribution:

```text
standardized difference =
    NCI-standardized mtDNA score
    - NCI-standardized nuclear OXPHOS score
```

This detects whether one compartment is relatively higher or lower than the other.

For example:

```text
mtDNA z-score       = -0.8
nuclear OXPHOS      =  0.2
difference          = -1.0
```

This donor has a lower mtDNA signal relative to the nuclear signal.

### 3.2 Endpoint 2: NCI-reference residual

Fit the normal relationship using NCI donors:

```text
mtDNA score ~ nuclear OXPHOS score + sex + APOE + age + PMI
```

Then calculate for every donor:

```text
residual = observed mtDNA score - predicted mtDNA score
```

A systematic AD-versus-NCI residual difference means that AD donors depart from the relationship expected from NCI donors.

This is also the preferred shared endpoint used to connect the three candidate systems to C3.

### 3.3 Endpoint 3: Coupling-slope change

This analysis asks whether the strength of the relationship changes.

Conceptually:

```text
NCI: mtDNA rises strongly as nuclear OXPHOS rises
AD:  mtDNA rises weakly, differently, or not at all
```

The statistical test directly compares the mtDNA-versus-nuclear slope between the planned groups.

These three endpoints are specified in [Task 4](../mitochondrial_deep_dive_next_steps_plan.md#task-4-test-the-mtdna-nuclear-relationship).

## 4. What is required for C3 to pass?

Gate 2 requires:

1. At least two of the three endpoints must have `q <= 0.05`.
2. Those endpoints must point in biologically compatible directions.
3. At least one passing endpoint must be:

   - the NCI-reference residual; or
   - the coupling-slope change.

4. The result must agree when scores are constructed using the alternative NCI-trained PC1 method.
5. The result must survive the prespecified RNA-quality sensitivities.

The authoritative rule is in [Gate 2](../mitochondrial_deep_dive_next_steps_plan.md#8-the-round-1-gate-rules).

Additional checks include:

- donor bootstrap;
- leave-one-donor-out analysis;
- balancing donor and nucleus counts;
- profiles with at least 50 nuclei;
- removing each mtDNA gene in turn;
- examining individual OXPHOS complexes;
- mitochondrial-read-fraction adjustment;
- excluding prespecified low-quality profiles.

The modifier-specific analysis covers three endpoints x seven frozen modifier comparisons x three broad cell classes, so the plan adjusts 63 primary tests together rather than correcting only the interesting results.

## 5. General C3 versus modifier-specific C3

There are two levels of wording:

- A general AD-versus-NCI C3 result supports:  
  “AD is associated with an altered mitonuclear expression relationship.”
- A direct AD-by-sex or AD-by-APOE C3 contrast supports:  
  “The AD-related mitonuclear alteration differs by sex or APOE.”

A general AD effect cannot support the second sentence. The relevant direct modifier contrast must also pass.

## 6. What data are not required to establish C3?

The following are not needed for the initial, internally supported C3 test:

- the three candidate systems;
- KDA or network results;
- protein data;
- new human samples;
- laboratory perturbation experiments.

C3 must be tested independently of `APOE-TUFM`, `LAMTOR5-ATP5IF1`, and `GABARAPL2-CHCHD2/PARK7`. Those candidates are subsequently tested for association with the C3 endpoint.

## 7. What C3 would and would not establish

If Gate 2 passes, the defensible conclusion is:

> AD is associated with an altered mitonuclear transcriptional relationship.

C3 alone does not demonstrate:

- impaired oxygen consumption;
- reduced ATP production;
- altered mitochondrial mass;
- organelle dysfunction;
- causation by AD or any candidate gene.

Those stronger conclusions require functional mitochondrial measurements and, for causation, perturbation/rescue experiments. The main plan explicitly limits C3 to RNA-abundance relationships.

---

## 8. Required breakdown by cell type, sex, and APOE

As the plan is currently written, the primary C3 analysis uses:

- three broad cell classes, not all 54 fine cell types;
- seven direct sex/APOE modifier contrasts;
- three mitonuclear endpoints.

That produces:

```text
3 endpoints x 7 modifiers x 3 broad cell classes = 63 primary tests
```

### 8.1 Cell-type level

The primary C3 cell contexts are:

1. Astrocytes
2. Excitatory neurons
3. Inhibitory neurons

The 54 fine cell types are used to construct and validate the broad pseudobulk profiles, but they do not carry the primary C3 inference.

Fine types can be used only as prespecified localization analyses—for example, asking whether an excitatory-neuron result appears strongest in a particular RORB subtype. They cannot rescue a failed broad-class result. The plan explicitly excludes “all-54-fine-cell primary claims” in its [scope exclusions](../mitochondrial_deep_dive_next_steps_plan.md#13-work-that-is-not-part-of-round-1).

The hierarchy is therefore:

```text
Primary C3 inference
|-- Astrocytes
|-- Excitatory neurons
`-- Inhibitory neurons

Optional localization
`-- Selected prespecified fine types, not all 54
```

### 8.2 Sex and APOE breakdown

The plan does not simply run an AD-versus-NCI test separately in every subgroup and compare which subgroup is significant. Instead, within each broad cell class, it estimates direct interaction contrasts.

#### Does sex modify the AD effect?

1. Female-versus-male difference in the AD effect within APOE ε2
2. Female-versus-male difference within APOE ε3/ε3
3. Female-versus-male difference within APOE ε4

For example:

```text
(AD - NCI in females with ε4)
-
(AD - NCI in males with ε4)
```

#### Does APOE modify the AD effect?

4. ε2 versus ε3/ε3 within females
5. ε2 versus ε3/ε3 within males
6. ε4 versus ε3/ε3 within females
7. ε4 versus ε3/ε3 within males

For example:

```text
(AD - NCI in ε4 females)
-
(AD - NCI in ε3/ε3 females)
```

These are listed in the [Round 0 specifications](../mitochondrial_deep_dive_next_steps_plan.md#round-0a-freeze-the-rules).

Two additional three-way tests—whether APOE changes the sex difference—are secondary unless the planned claim specifically requires that wording.

### 8.3 How the NCI reference is constructed

The NCI relationship should be fitted separately for each broad cell class, but it does not need to be fitted separately within every sex-by-APOE subgroup.

For example, fit one astrocyte reference model using all eligible NCI astrocyte donors:

```text
mtDNA score ~ nuclear OXPHOS score + sex + APOE + age + PMI
```

Then repeat for:

- excitatory neurons;
- inhibitory neurons.

Sex and APOE are included in the reference model as covariates. After calculating the mitonuclear endpoints, the planned direct AD-by-sex and AD-by-APOE contrasts are tested.

This approach avoids estimating unstable reference relationships in very small subgroups.

## 9. C3 versus C2

Analyzing C3 separately in three broad cell classes does not establish that the cell types differ.

For example:

```text
C3 passes in astrocytes
C3 does not pass in neurons
```

does not prove that the astrocyte and neuronal effects are different. C2 requires a direct between-cell comparison.

Therefore:

- C3 asks whether the mitonuclear relationship changes within a cell context.
- C2 asks whether that change is statistically different between cell contexts.

## 10. Ambiguity in the current plan

The documents say C3 can pass even if C1—the sex/APOE modifier claim—fails. That requires a general adjusted AD-versus-NCI C3 test.

However, Task 4's stated primary family currently contains only:

```text
3 endpoints x 7 sex/APOE modifiers x 3 broad classes
```

That operationalizes modifier-specific C3, not a clean general C3 test.

For full logical consistency, the plan should distinguish:

| Analysis | Tests | Claim supported |
|---|---:|---|
| General C3 | 3 endpoints x 3 broad classes = 9 | AD changes the mitonuclear relationship |
| Modifier-specific C3 | 3 endpoints x 7 modifiers x 3 broad classes = 63 | The AD-related mitonuclear change differs by sex or APOE |

The two families should have separately prespecified multiple-testing rules. Otherwise, it is unclear how C3 could pass when C1 fails.

In summary, use the three broad cell classes for primary C3, not all 54 fine types. Use sex and APOE direct contrasts when testing the modifier-specific form of C3, and add an explicit overall AD-versus-NCI analysis if the project wants C3 to stand independently of C1.
