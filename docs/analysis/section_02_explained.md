# Tutorial: understanding Section 2, “AD-associated OXPHOS direction varies across sex/APOE strata”

**Source section:** [Joint Phase 11–12 synthesis](phase11_phase12_joint_mitochondrial_discussion.md)  
**Audience:** readers with a high-school-level biology background  
**Purpose:** explain every sentence and every table entry in Section 2 without
adding a stronger claim than the data support

## 1. The central idea in one paragraph

Mitochondria are structures inside cells that help turn nutrients and oxygen
into ATP, the cell's usable energy. OXPHOS—short for **oxidative
phosphorylation**—is the final, power-producing part of this process. Section 2
asks whether the RNA instructions for OXPHOS machinery differ between
Alzheimer's disease (AD) and no cognitive impairment (NCI), and whether the
answer looks different after people are separated by sex and APOE group. The
main observation is that there is no single AD-associated direction:
female-ε2 samples are mainly AD-up, male-ε2 and female-ε4 samples are mainly
AD-down, and the remaining groups are weaker or more mixed.

This is a result about **RNA abundance in postmortem brain-cell populations**.
It is not yet a result about ATP output, cause of disease, protection from
disease, or treatment response.

## 2. Vocabulary needed before reading the section

| Term | Tutorial definition |
|---|---|
| **AD** | Alzheimer's disease. In this analysis, AD samples are compared with NCI samples. |
| **NCI** | No cognitive impairment. This is the comparison group within each sex/APOE stratum. |
| **Mitochondrion** | A structure inside a cell that performs many metabolic jobs, including most ATP production. The plural is *mitochondria*. |
| **ATP** | A small molecule cells use as an immediately available energy source. |
| **OXPHOS** | Oxidative phosphorylation: respiratory-chain complexes I–IV build a proton gradient, and Complex V uses that gradient to make ATP. |
| **Gene expression** | The process of using a gene to make RNA and usually protein. This study measures RNA, not the final amount or activity of protein. |
| **Transcription** | The production of RNA from DNA. “More transcription” generally means more RNA copies were detected. |
| **DEG** | Differentially expressed gene: a gene whose RNA differs enough between AD and NCI to pass the study's size and statistical thresholds. |
| **AD-up** | RNA is significantly higher in AD than in NCI within the same sex/APOE group and cell type. |
| **AD-down** | RNA is significantly lower in AD than in NCI within the same sex/APOE group and cell type. |
| **APOE** | A gene with common inherited versions called ε2, ε3, and ε4. These variants are associated with different AD risks, but risk is not the same thing as the mitochondrial RNA response measured here. |
| **Stratum** | One analysis group defined here by sex and APOE, such as female ε2 or male ε3/ε3. The plural is *strata*. |
| **Cell type** | A specialized kind of brain cell, such as an excitatory neuron or astrocyte. Fine cell types subdivide these broad categories. |
| **Donor** | One person who contributed a brain sample. Donors—not individual nuclei—are the biological replicates. |
| **mtDNA** | Mitochondrial DNA, the small genome located inside mitochondria. It encodes 13 OXPHOS proteins. |
| **Nuclear DNA** | DNA in the cell nucleus. It encodes the other 89 genes in the 102-gene MitoCarta OXPHOS-subunit set used here. |

### What counts as a DEG in this analysis?

A gene–cell-type result was called a DEG only when it satisfied both:

1. an absolute log2 fold change greater than `log2(1.3)`. In ordinary ratios,
   AD RNA had to be more than 1.3 times NCI RNA for an AD-up call, or less than
   `1 / 1.3 ≈ 0.769` times NCI RNA for an AD-down call; and
2. a within-comparison Benjamini–Hochberg false-discovery rate below 0.05.

The second rule adjusts for testing many genes. Passing it means the result is
unlikely under the study's statistical null model; it does not prove causation
or guarantee a large change in cell function.

## 3. How one table count is produced

The analysis can be pictured as:

> choose one sex/APOE stratum → choose one fine cell type → compare AD with
> NCI → test one mitochondrial gene → classify it as AD-up, unchanged by the
> threshold, or AD-down

This is repeated across genes and fine cell types.

A **gene–cell-type occurrence** is one gene tested in one fine cell type. If
`COX5B` is AD-up in three fine cell types, that contributes three AD-up
occurrences. Therefore:

- an occurrence is not a person;
- an occurrence is not necessarily a unique gene; and
- recurrence across cell types is not the same as replication in another
  cohort.

## 4. The title, phrase by phrase

> **AD-associated OXPHOS direction varies across sex/APOE strata — [New
> descriptive pathway discovery and same-resource extension of Yu]**

### “AD-associated”

The study compares AD with NCI. It observes an association with AD status, not
proof that AD caused the RNA change or that the RNA change caused AD.

### “OXPHOS direction”

Direction means whether significant OXPHOS RNA changes point mainly upward or
downward in AD:

- upward: AD has more RNA than NCI;
- downward: AD has less RNA than NCI; and
- mixed: substantial numbers point in both directions.

### “Varies across sex/APOE strata”

The direction is not the same in all six analysis groups. This is descriptive:
the study analyzed the groups separately but did not yet fit the formal
interaction model needed to prove that sex or APOE statistically modifies the
AD effect.

### “New descriptive pathway discovery”

The complete six-group directional pattern was not found in the targeted
literature review. “Descriptive” is important: the pattern was observed and
summarized, but its causal explanation has not been demonstrated.

### “Same-resource extension of Yu”

Yu and colleagues previously analyzed sex/APOE differences across the
transcriptome using the same ROSMAP resource. The present result narrows that
question to mitochondrial and OXPHOS genes. It adds pathway detail but is not
an independent replication because the participant resource overlaps.

## 5. Discovery paragraph, sentence by sentence

### Sentence 1

> **“AD-associated mitochondrial transcription varies descriptively across
> sex/APOE strata and cell types: female ε2 is predominantly OXPHOS-up, male ε2
> and female ε4 are predominantly OXPHOS-down, and male ε4 is mixed with
> selected excitatory-neuron increases.”**

#### Plain-language translation

When AD and NCI are compared separately within each group, the RNA instructions
for mitochondrial energy machinery do not change in one universal direction.
The overall pattern depends on which sex/APOE group and which brain-cell type
is being examined.

#### Phrase-by-phrase explanation

- **“Mitochondrial transcription”** means the measured amount of RNA from
  mitochondrial-related genes. Most of these genes are located in the nucleus;
  a smaller group is located in mtDNA.
- **“Varies descriptively”** means the separate group summaries look
  different. It does not mean a formal interaction test is already
  significant.
- **“Female ε2 is predominantly OXPHOS-up”** means that among significant
  female-ε2 OXPHOS occurrences, 398 are higher in AD and only 5 are lower.
- **“Male ε2 ... predominantly OXPHOS-down”** means 564 significant
  occurrences are lower in AD and 95 are higher.
- **“Female ε4 ... predominantly OXPHOS-down”** means 274 are lower and 50
  are higher.
- **“Male ε4 is mixed”** means both directions occur: 141 up and 86 down.
  The upward observations are concentrated in selected neuronal populations,
  not uniformly distributed across every brain cell.
- **“Excitatory neurons”** are neurons that generally increase the chance that
  their target cells will fire. They are not all equivalent; the analysis
  distinguishes fine subtypes by cortical layer and marker genes.

#### What this sentence does not mean

- It does not say that all female-ε2 OXPHOS genes are up.
- It does not say every cell type follows the group-level majority.
- It does not say higher OXPHOS RNA produces more ATP.
- It does not prove that sex or APOE causes the directional difference.

### Sentence 2

> **“Male ε2 has the largest mitochondrial DEG burden.”**

#### Plain-language translation

Of the six strata, male ε2 has the greatest number and fraction of
mitochondrial gene–cell-type tests that meet the DEG criteria.

#### The relevant calculation

Male ε2 has:

- 3,753 significant mitochondrial occurrences out of 35,380 tested;
- \(3,753 / 35,380 = 10.61\%\); and
- 659 significant OXPHOS occurrences out of 3,505 tested, or 18.80%.

Both percentages are the largest among the six strata.

#### Why “burden” needs care

Here, burden means **number of detected RNA changes**, not disease severity,
number of damaged mitochondria, or amount of cognitive decline. Male ε2 also
has the smallest major donor group—7 AD and 6 NCI donors—so unusually large
counts may combine real biology with statistical instability.

## 6. Conclusion paragraph, sentence by sentence

### Sentence 3

> **“The complete directional pattern is the principal Phase 11 discovery and
> the context in which all Phase 12 neighborhoods should be interpreted.”**

#### Plain-language translation

The most important Phase 11 observation is not simply “OXPHOS changes in AD.”
It is that the direction differs among the six groups. Phase 12 network results
must therefore be read in the appropriate group and cell type.

For example, a Phase 12 neighborhood enriched for a female-ε2 AD-up signature
and one enriched for a male-ε2 AD-down signature can contain some of the same
OXPHOS machinery while representing opposite RNA directions.

#### Why this matters

Ignoring the stratum could average together opposite patterns and produce a
misleading “no change” result. Conversely, combining all Phase 12 candidate
calls without their query direction could make a candidate look universally
important when its supporting signatures differ by context.

### Sentence 4

> **“Prior work supports sex-, APOE-, and cell-dependent metabolic
> heterogeneity, but the targeted review found no independent study
> reproducing the full female-ε2-up/male-ε2-down/female-ε4-down/male-ε4-mixed
> AD contrast.”**

#### Plain-language translation

Other research gives good reasons to expect metabolism to vary with sex, APOE,
and cell type. However, the literature search did not find a separate study
that reproduced this exact four-part AD-associated OXPHOS pattern.

#### “Supports the pieces” versus “reproduces the whole pattern”

These are different evidence levels:

- A paper showing that APOE4 changes astrocyte metabolism supports one
  biological component.
- A paper showing sex-dependent mitochondrial function supports another.
- To reproduce this result, an independent study would need comparable AD and
  NCI samples, sex/APOE groups including ε2, suitable brain-cell resolution,
  and the same directional OXPHOS result.

The targeted review found the first two types of evidence, but not the third.

### Sentence 5

> **“The large male-ε2 mitochondrial subset extends the parent
> transcriptome-wide result in the same data resource.”**

#### Plain-language translation

The earlier Yu analysis found that male ε2 was transcriptionally distinctive
when considering genes across the transcriptome. The mitochondrial analysis
shows that mitochondrial genes make a substantial contribution to that broad
signal.

#### Why this is an extension, not replication

The new analysis asks a more specific question of the same underlying ROSMAP
resource. It adds biological interpretation—mitochondrial and OXPHOS pathway
direction—but does not provide new participants who could independently
confirm the result.

### Sentence 6

> **“Both findings remain descriptive until donor-aware interaction testing
> and independent-cohort replication.”**

#### “Both findings”

This refers to:

1. the directional OXPHOS pattern across the six strata; and
2. the unusually large male-ε2 mitochondrial response.

#### “Donor-aware”

Thousands of nuclei can come from one donor. Treating all those nuclei as
fully independent would make the effective sample size look larger than the
number of people. A donor-aware analysis preserves the person as the
biological replicate.

#### “Interaction testing”

A formal interaction test asks whether the AD–NCI difference itself changes
with sex or APOE. It is stronger than observing significance in one group and
not another.

#### “Independent-cohort replication”

The leading directions should be tested in a different set of people,
preferably with a comparable brain region, diagnosis, cell-type resolution,
and analysis design.

## 7. Data table tutorial

### What each column means

| Column | Meaning |
|---|---|
| **Stratum** | The sex/APOE group analyzed separately. |
| **Mitochondrial DEG occurrences / tested** | Significant gene–cell-type results divided by all eligible mitochondrial gene–cell-type tests. |
| **AD up / down** | Among the significant mitochondrial occurrences, how many have more versus less RNA in AD than NCI. These two numbers sum to the mitochondrial DEG numerator. |
| **OXPHOS occurrences / tested** | The same calculation restricted to the 102 MitoCarta OXPHOS-subunit genes. |
| **OXPHOS up / down** | Direction among significant OXPHOS occurrences. These two numbers sum to the OXPHOS numerator. |

Denominators differ slightly among strata because not every gene is detected
or testable in every fine cell type, and three male-ε2 cell-type contrasts were
not estimable.

### Worked example: female ε2

The female-ε2 row is:

| Stratum | Mitochondrial DEG occurrences / tested | AD up / down | OXPHOS occurrences / tested | OXPHOS up / down |
|---|---:|---:|---:|---:|
| Female ε2 | 1,128 / 37,647 | 935 / 193 | 403 / 3,736 | 398 / 5 |

Read it step by step:

1. There were 37,647 eligible mitochondrial gene–cell-type tests.
2. Of those, 1,128 passed the DEG criteria: \(1,128 / 37,647 = 3.00\%\).
3. Among the 1,128 significant mitochondrial occurrences, 935 were AD-up and
   193 were AD-down.
4. Restricting the analysis to OXPHOS subunits gives 3,736 eligible tests.
5. Of those, 403 were significant: \(403 / 3,736 = 10.79\%\).
6. Among the 403 significant OXPHOS occurrences, 398 were AD-up and 5 were
   AD-down.
7. Therefore, \(398 / 403 = 98.8\%\) of the significant OXPHOS occurrences
   pointed upward.

The 398 observations come from 66 unique genes appearing across multiple cell
types. The five AD-down observations involve four genes:

- `MT-ND4L` in `Ast CHI3L1`;
- `UQCRFS1` in `Inh ALCAM TRPM3`;
- `NDUFB5` in `Inh LAMP5 NRG1 (Rosehip)`;
- `NDUFA5` in `Inh LAMP5 NRG1 (Rosehip)`; and
- `UQCRFS1` again in `Inh LAMP5 NRG1 (Rosehip)`.

`MT-ND4L` and `UQCRFS1` are AD-up in other female-ε2 cell types, showing why a
gene can contribute observations in both directions across different cells.

### Interpreting all six rows

| Stratum | Significant mitochondrial tests | Significant OXPHOS tests | Direction among significant OXPHOS occurrences | Tutorial interpretation |
|---|---:|---:|---:|---|
| Female ε2 | 3.00% | 10.79% | 98.8% up / 1.2% down | Strongly AD-up among detected OXPHOS changes |
| Female ε3/ε3 | 2.23% | 9.03% | 96.1% up / 3.9% down | Also strongly AD-up, with fewer total changes than female ε2 |
| Female ε4 | 4.41% | 8.90% | 15.4% up / 84.6% down | Strongly AD-down |
| Male ε2 | 10.61% | 18.80% | 14.4% up / 85.6% down | Largest detected burden and strongly AD-down |
| Male ε3/ε3 | 2.46% | 4.84% | 49.7% up / 50.3% down | Nearly exactly balanced |
| Male ε4 | 3.00% | 6.32% | 62.1% up / 37.9% down | Mixed, with more up than down |

### What are the OXPHOS genes?

The count uses the 102-gene MitoCarta “OXPHOS subunits” set:

- **Complex I:** `NDUFA*`, `NDUFB*`, `NDUFC*`, `NDUFS*`, `NDUFV*`, and
  `MT-ND1` through `MT-ND6` plus `MT-ND4L`;
- **Complex II:** `SDHA`, `SDHB`, `SDHC`, and `SDHD`;
- **Complex III:** `UQCR*`, `CYC1`, and `MT-CYB`;
- **Complex IV:** `COX*`, `MT-CO1`, `MT-CO2`, `MT-CO3`, and `NDUFA4`;
- **Complex V:** `ATP5*`, `ATP5IF1`, `MT-ATP6`, and `MT-ATP8`; and
- **electron-transfer/support genes:** including `CYCS` and `HCCS`.

The exact stored list is in
[`mitocarta_pathways.gmt`](../../results/minerva_production/03_annotations/mitocarta_pathways.gmt).

### The most important table-reading caution

The table describes RNA direction among results that passed a threshold.
It does not directly report:

- oxygen consumption;
- ATP production;
- respiratory-complex protein abundance or activity;
- mitochondrial number;
- disease severity; or
- whether the response is helpful or harmful.

## 8. Evidence immediately after the table, sentence by sentence

### Sentence 7

> **“The effect is not an mtDNA-only artifact.”**

#### Why this question matters

mtDNA transcripts can be abundant and sensitive to mitochondrial content, RNA
quality, cell stress, and postmortem conditions. Because 13 OXPHOS proteins are
encoded by mtDNA, those genes could produce a strong-looking signal even if
the much larger nuclear program did not agree.

#### What the sentence means

The authors repeated the directional summary after excluding all mtDNA-encoded
OXPHOS subunits. The major female-ε2, female-ε4, and male-ε2 directions
remained. Therefore, the pattern is not generated only by the 13 mtDNA genes.

“Not mtDNA-only” does not mean all technical concerns are eliminated.

### Sentence 8

> **“After excluding mtDNA-encoded subunits, nuclear OXPHOS occurrences remain
> strongly upward in female ε2 (`258 up / 4 down`) and downward in female ε4
> (`17 / 234`) and male ε2 (`77 / 444`).”**

#### Plain-language translation

Most OXPHOS proteins are encoded by genes in the nucleus. Looking only at
those nuclear genes gives the same main directions:

| Stratum | Nuclear OXPHOS up / down | Percentage in majority direction |
|---|---:|---:|
| Female ε2 | 258 / 4 | 98.5% up |
| Female ε4 | 17 / 234 | 93.2% down |
| Male ε2 | 77 / 444 | 85.2% down |

This makes a simple mtDNA-abundance explanation less likely. It still does not
prove corresponding changes in OXPHOS protein assembly or respiratory flux.

### Sentence 9

> **“The clearest paired pattern is APOE ε2: 153 OXPHOS gene–cell-type
> occurrences are female-up/male-down.”**

#### What “paired” means

For the same OXPHOS gene in the same fine cell type:

- AD versus NCI is significantly upward in female ε2; and
- AD versus NCI is significantly downward in male ε2.

That exact opposite state occurs 153 times. It is more specific than merely
being significant in one group and nonsignificant in the other.

#### What “paired” does not mean

It is not a direct female-versus-male expression comparison and not yet a
formal AD-by-sex interaction. It is a comparison of two separately estimated
AD-versus-NCI results.

### Sentence 10

> **“`Exc L3-4 RORB CUX2` contains 33 of these reversals—31 nuclear encoded
> plus `MT-ND2` and `MT-ND4`.”**

#### Decoding the cell-type label

- **`Exc`** means excitatory neuron.
- **`L3-4`** means the subtype is associated with cortical layers 3 and 4.
- **`RORB` and `CUX2`** are marker genes used to identify this neuronal
  population.

Of the 153 female-up/male-down ε2 occurrences, 33 occur in this one neuronal
subtype. Thirty-one are encoded in nuclear DNA, while `MT-ND2` and `MT-ND4`
are encoded by mtDNA. This concentration helps identify a specific cell
population for follow-up experiments.

It does not mean that this cell type alone explains the whole-brain pattern.

### Sentence 11

> **“Female-ε4/male-ε4 reversals concentrate in `Exc RELN CHD7`, while
> female-ε4-only loss is prominent in `Exc L2-3 CBLN2 LINC02306`.”**

#### Plain-language translation

The ε4-associated sex difference is not uniform across all neurons:

- `Exc RELN CHD7` contains many cases where female and male ε4 AD effects
  point in opposite directions; and
- `Exc L2-3 CBLN2 LINC02306` contains many OXPHOS decreases detected in female
  ε4 but not as threshold-level decreases in male ε4.

#### Why “female-ε4-only loss” needs care

“Only” means only female ε4 crossed the study's DEG threshold. The male ε4
effect could be small, variable, or underpowered rather than exactly zero.
“Loss” refers to lower RNA abundance, not direct loss of neurons, mitochondria,
or respiratory function.

## 9. Prior-work paragraph, sentence by sentence

### Sentence 12

> **“The parent transcriptome-wide ROSMAP analysis found extensive
> APOE-genotype-dependent sex differences (Yu et al., 2026); this mitochondrial
> restriction supplies pathway specificity and direction but is not an
> independent dataset.”**

#### What the parent study did

The Yu study examined expression across the transcriptome rather than focusing
only on mitochondria. It established that sex-related AD expression patterns
can depend on APOE genotype.

#### What the mitochondrial restriction adds

The present analysis identifies:

- OXPHOS as a dominant pathway;
- the AD-up or AD-down direction within each stratum;
- the fine cell types with concentrated reversals; and
- candidate mitochondrial genes for follow-up.

#### Why it is not independent

Both analyses use the ROSMAP resource. A new analysis of the same resource can
refine a finding, but it cannot show that the finding repeats in new
participants.

See [Yu et al., 2026](https://doi.org/10.1002/alz.71463).

### Sentence 13

> **“A separate sex-stratified single-cell reanalysis reported
> female-down/male-up mitochondrial and coupled electron/ATP programs in
> entorhinal neurons (Belonwu et al., 2022), which resembles selected ε4
> populations but conflicts with the ε2 direction.”**

#### Plain-language translation

Another analysis found lower mitochondrial programs in female AD neurons and
higher programs in male AD neurons. That resembles parts of the present ε4
result, but it is opposite to the present ε2 result, where female ε2 is mostly
up and male ε2 is mostly down.

#### Why disagreement is informative

The studies can differ because of:

- brain region;
- neuronal subtype;
- APOE composition;
- participant selection;
- statistical method; or
- disease stage.

The disagreement argues against a simple rule such as “female AD is always
OXPHOS-down.”

See [Belonwu et al., 2022](https://doi.org/10.1007/s12035-021-02591-8).

### Sentence 14

> **“Clinical and metabolic studies justify stratification without
> reproducing the local contrast.”**

#### Plain-language translation

Previous studies show that separating participants by sex and APOE is
scientifically reasonable. However, those studies do not confirm this exact
brain-cell OXPHOS pattern.

“Justify stratification” means “give a reason to analyze the groups
separately.” It does not mean “prove the result.”

### Sentence 15

> **“APOE-related clinical effects vary with sex and age.”**

#### Plain-language translation

APOE genotype does not act as a fixed risk multiplier that is identical for
every person. In the cited studies, the association between an APOE genotype
and an AD-related outcome differed between women and men, and some of the sex
difference appeared only within a particular age range.

Here, **“effects” means statistical associations in groups of people**. It
does not mean that these studies directly measured what APOE did to a
mitochondrion.

#### What is being compared?

Each person has two APOE copies. The common combinations discussed here
include:

- **ε3/ε3**, generally used as the reference group;
- **ε3/ε4**, which contains one ε4 copy and is associated with higher AD risk;
  and
- **ε2/ε3**, which contains one ε2 copy and is associated with lower AD risk
  on average.

A sex-specific estimate compares women with one genotype against women in the
reference genotype, and separately makes the corresponding comparison among
men. Researchers then use an **APOE-by-sex interaction test** to ask whether
the two genotype associations differ by more than would be expected from
sampling variation. A result being significant in women but not in men is not,
by itself, proof of such a difference; the interaction is the relevant test.

#### What Altmann et al. found

Altmann and colleagues pooled longitudinal cohorts and asked whether carrying
ε4 was associated with clinical conversion:

- Among 5,496 initially cognitively normal participants, ε4 carriers had a
  higher rate of conversion to mild cognitive impairment or AD. The estimated
  hazard ratio was **1.81 in women** and **1.27 in men**, and the
  APOE-by-sex interaction was significant (`p = 0.011`).
- Among 2,588 participants who already had mild cognitive impairment, the
  hazard ratios for conversion to AD were **2.16 in women** and **1.64 in
  men**. In the full analysis, however, the interaction was not significant
  (`p = 0.14`). This is an important reminder that two different-looking
  estimates do not automatically establish a sex difference.
- In a cerebrospinal-fluid subset with mild cognitive impairment, ε4 was
  associated with a more AD-like total-tau level and tau-to-amyloid-β ratio in
  women than in men.

A hazard ratio of 1.81 does **not** mean that 81% of women developed AD. It
means that, under that study's time-to-event model, the estimated conversion
rate for female ε4 carriers was 1.81 times the rate for the female reference
group during follow-up.

#### What Neu et al. added about age

Neu and colleagues combined 27 studies with nearly 58,000 participants. Their
larger analysis made the sex result more specific:

- Across the full **55–85-year** range, the AD odds associated with ε3/ε4 did
  not differ significantly between women and men.
- Within approximately **65–75 years**, ε3/ε4 was associated with higher AD
  odds in women than in men.
- ε2/ε3 was associated with lower AD odds in both sexes, but the association
  was stronger in women: the odds ratio was **0.51 in women** and **0.71 in
  men**, relative to ε3/ε3 in the same sex (`APOE-by-sex p = 0.01`).

An odds ratio of 0.51 means approximately 49% lower **odds** than the reference
group; it does not mean a 51% chance of AD or guarantee protection for an
individual. Similarly, the 65–75 result does not mean that APOE suddenly
switches on at age 65 or off at age 75. It means that the detectable sex
difference was concentrated in that age window in those data.

#### How to read the original sentence

The sentence therefore says:

> The clinical association of an APOE genotype is context-dependent; its
> estimated size can differ by sex and by the ages included in the analysis.

It does **not** say:

- every female ε4 carrier has greater risk than every male ε4 carrier;
- APOE genotype alone determines whether someone develops AD;
- ε2 prevents AD in every carrier; or
- sex and age have already been shown to cause the OXPHOS RNA directions in
  this study.

#### Why this is indirect evidence

Clinical risk is not the same measurement as OXPHOS RNA in a particular brain
cell. The cited results justify keeping sex and APOE groups separate instead of
assuming one universal APOE association. They do not show that the female-ε2
OXPHOS-up pattern is protective, that the male-ε2 OXPHOS-down pattern is
harmful, or that mitochondrial transcription explains the reported clinical
risk differences.

See [Altmann et al., 2014](https://doi.org/10.1002/ana.24135) and
[Neu et al., 2017](https://doi.org/10.1001/jamaneurol.2017.2188).

### Sentence 16

> **“Female APOE4 carriers showed greater hypometabolism in one imaging study,
> and sex and APOE4 affected brain high-energy phosphate ratios in midlife
> adults.”**

#### “Hypometabolism”

Hypometabolism means lower use of glucose in a brain region, commonly measured
with FDG-PET imaging. It suggests altered energy use but is not a direct
measurement of OXPHOS gene expression.

#### “High-energy phosphate ratios”

ATP, phosphocreatine, and inorganic phosphate can be studied with phosphorus
magnetic-resonance spectroscopy. Their ratios provide information about brain
energy state, but they are not interchangeable with RNA levels.

These studies make the female-ε4 energy-vulnerability interpretation
plausible, while stopping short of reproducing the local cell-type result.

See [Sampedro et al., 2015](https://doi.org/10.18632/oncotarget.5185) and
[Jett et al., 2023](https://doi.org/10.1371/journal.pone.0281302).

### Sentence 17

> **“Human iPSC-derived AD models also show cell- and sex-dependent
> mitochondrial phenotypes, and a 2026 APOE-targeted mouse study found sex- and
> diet-dependent effects on mitochondrial function.”**

#### iPSC-derived models

Researchers can reprogram human cells into induced pluripotent stem cells
(iPSCs) and then produce neuron-like or astrocyte-like cells. These models
allow controlled experiments and show that mitochondrial effects can depend on
cell type and sex background.

#### APOE-targeted mice

Mice engineered to carry human APOE variants allow experiments that cannot be
performed in living human brains. The cited study found that sex and diet
changed APOE-related mitochondrial phenotypes.

#### Why these studies do not replicate the result

Cultured cells and mice differ from postmortem human brain. They support
biological plausibility, not the exact six-stratum AD-versus-NCI pattern.

See [Flannagan et al., 2023](https://doi.org/10.3389/fnmol.2023.1201015) and
[Johnson et al., 2026](https://doi.org/10.1096/fba.2026-00121).

### Sentence 18

> **“Female human-APOE2 mouse brain had the most robust glucose-metabolic
> profile, but that experiment did not include male APOE2 animals or an AD
> contrast.”**

#### What the result contributes

It provides evidence that female APOE2 brain can have a distinctive metabolic
profile, which is compatible with the strong female-ε2 signal observed here.

#### Why the missing groups matter

Without male APOE2 mice, the experiment cannot test the female-up/male-down ε2
pattern. Without an AD-versus-control disease comparison, it cannot test an
AD-associated direction at all. It is contextual evidence, not confirmation.

See [Wu et al., 2018](https://doi.org/10.1523/JNEUROSCI.2262-17.2018).

## 10. Limitations and decisive tests, sentence by sentence

### Sentence 19

> **“Male ε2 contains only 7 AD and 6 NCI donors, and the source model does not
> model donors as biological replicates.”**

#### Why 13 donors is a concern

With small groups:

- one unusual donor can strongly influence the average;
- estimates have more uncertainty;
- cell availability can differ sharply among donors; and
- a large number of nuclei cannot fully replace a larger number of people.

#### Why nuclei are not biological replicates

Many nuclei from one brain share the same person's genetics, exposures, age,
and disease history. They provide detailed cellular measurements but are not
independent people. The statistical analysis should preserve donor identity
when estimating population-level uncertainty.

This limitation is especially important because male ε2 produces the largest
DEG burden.

### Sentence 20

> **“Build donor-by-cell-type pseudobulk profiles and fit AD-by-sex within
> APOE, AD-by-APOE within sex, and—where estimable—the three-way interaction.”**

#### Donor-by-cell-type pseudobulk

For each donor and fine cell type, RNA counts from that donor's nuclei are
combined into one profile. The unit entering the group-level model is then the
donor rather than each nucleus.

#### AD-by-sex within APOE

Within one APOE group, test whether the AD–NCI difference is statistically
different between females and males.

For ε2, the question is not merely:

> Is female ε2 significant, and is male ε2 significant?

It is:

> Is the female ε2 AD effect statistically different from the male ε2 AD
> effect?

#### AD-by-APOE within sex

Within females or within males, test whether the AD–NCI difference changes
among ε2, ε3/ε3, and ε4 groups.

#### Three-way interaction

Test whether the way sex changes the AD effect itself depends on APOE group.
This is the formal statistical version of the complete sex × APOE × AD
hypothesis.

#### “Where estimable”

A model can estimate an interaction only when there are enough donors and
usable observations in the required combinations. The small male-ε2 group may
make some fine-cell-type tests unstable or impossible.

### Sentence 21

> **“Replicate the direction-aware OXPHOS result in another brain cohort before
> attaching protective or pathogenic meaning to any stratum.”**

#### “Direction-aware”

The replication must preserve AD-up versus AD-down information. Merely finding
that “OXPHOS is associated with AD” would not reproduce the central result.

#### “Another brain cohort”

Use a separate participant set so that the result is exposed to new biological
variation, sample processing, and measurement noise. Ideally, the cohort would
have:

- AD and NCI donors;
- sex and APOE information, including enough ε2 donors;
- a comparable brain region;
- single-cell or single-nucleus resolution; and
- sufficient donors in each group.

#### Why “protective” and “pathogenic” are premature

An AD-up OXPHOS RNA pattern could mean:

- successful compensation;
- an unsuccessful attempt to compensate;
- greater mitochondrial abundance;
- a stress response;
- selective survival of a particular cell state; or
- a technical or compositional effect.

An AD-down pattern could reflect respiratory failure, reduced mitochondrial
content, altered cell state, or disease consequence. RNA direction alone
cannot distinguish these explanations.

## 11. What Section 2 establishes—and what it does not

### Supported descriptive statements

- Significant OXPHOS RNA occurrences are overwhelmingly AD-up in female ε2
  and female ε3/ε3.
- They are overwhelmingly AD-down in female ε4 and male ε2.
- Male ε3/ε3 is nearly balanced, while male ε4 is mixed with more AD-up than
  AD-down occurrences.
- Male ε2 has the largest mitochondrial and OXPHOS DEG burden.
- The major directions persist after mtDNA-encoded subunits are removed.
- Exact ε2 female-up/male-down reversals concentrate in selected excitatory
  neuronal subtypes.

### Hypotheses that still require testing

- Sex statistically modifies the ε2-associated AD effect.
- APOE statistically modifies the sex-associated AD effect.
- The complete three-way AD × sex × APOE interaction is present.
- OXPHOS-up represents protection or successful compensation.
- OXPHOS-down represents impaired ATP production.
- Any observed transcript pattern causes AD pathology.

## 12. One-sentence takeaway

> In this dataset, the RNA instructions for mitochondrial energy production
> change in different directions across AD sex/APOE groups—most clearly
> female-ε2 up versus male-ε2 down—but donor-aware interaction tests,
> functional measurements, and an independent cohort are required before the
> pattern can be called a mechanism.

## 13. Local data and annotation sources

- [Joint Phase 11–12 discussion](phase11_phase12_joint_mitochondrial_discussion.md)
- [Phase 09 mitochondrial DEG results](../../results/minerva_production/09_annotate_genes/deg_mito_core.tsv.gz)
- [MitoCarta pathway definitions](../../results/minerva_production/03_annotations/mitocarta_pathways.gmt)
- [Phase 10 paired similarity states](../../results/minerva_production/10_similarity/mitochondrial_similarity_state_pairs.tsv.gz)
- [Phase 11 pathway results](../../results/minerva_production/11_pathway/similarity_tail_pathway_ora.tsv.gz)
