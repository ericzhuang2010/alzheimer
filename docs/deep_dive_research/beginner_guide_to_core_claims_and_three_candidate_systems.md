# Beginner's guide: how the main mitochondrial claims relate to the three candidate gene systems

**Prepared:** 2026-08-08

**Audience:** a reader with high-school biology and no assumed statistics or network-analysis background

**Purpose:** explain one part of the main research plan in much simpler language

**Status:** planning document; it does not report new experimental results

**Relationship to the main plan:** this is a teaching companion, not a replacement. It proposes one additional donor-level bridge analysis. That addition must be copied into the main plan and frozen before it becomes an official decision rule.

## The answer in everyday language

The main proposed finding about cellular energy and the three suggested groups of DNA instructions are two separate parts of the project.

First, use one measurement per person to test whether Alzheimer disease is related to a change in how two groups of energy-related DNA instructions work together. Also test whether that change differs between genetic groups, females and males, or kinds of brain cells.

Only after that should we test the three proposed gene systems. Each one must separately match the same prechosen measurement, pass checks showing that one person did not create the result, and beat fair chance comparisons in the gene map.

One gene system does not need to account for the entire result. If all three pass, we can say that three separately tested systems are associated with the same measured change. If only two pass, we name two. Computer analyses alone cannot show that any system causes the change.

## How to use this guide

Read the everyday-language answer above first. Then use Section 1 as a glossary whenever a word is unfamiliar; you do not need to memorize it before continuing.

- Read Sections 2–6 for the main explanation.
- Sections 7–9 contain optional technical details and decision rules.
- Sections 10–15 contain common mistakes, figures, checklists, writing, and the final recap.

The guide is detailed so that you can return to one section at a time. You do not need to memorize it.

---

## 1. Words to understand before reading the answer

This section defines the scientific and statistical words used later.

### 1.1 Basic biology words

**Cell**

The basic living unit of the body.

**DNA**

The molecule that stores genetic instructions in cells.

**Gene**

A section of DNA that contains instructions for making a biological product, often a protein.

**Protein**

A molecule that performs biological work in cells.

**RNA**

A molecule made when a cell reads DNA. Measuring RNA from a gene gives information about that gene's activity.

**Transcription, gene expression, and transcriptional change**

Transcription is the process of making RNA from a DNA instruction. **Gene expression** describes how a cell uses a gene's instructions. A transcriptional change means a change in measured RNA expression. It does not automatically mean that protein amount or cell function changed.

**RNA abundance**

How much RNA from a gene is measured in a sample. RNA amount and protein amount are not always the same.

**Nucleus and nuclear DNA**

The nucleus is the part of a human cell that stores most of its DNA. The plural is **nuclei**. DNA stored there is called **nuclear DNA**.

**Mitochondrion and mitochondria**

A mitochondrion is a structure inside a cell that helps convert energy from food into usable cellular energy. **Mitochondria** is the plural.

**Mitochondrial DNA, or mtDNA**

Mitochondria contain a small amount of their own DNA. Human mtDNA contains 13 genes that make protein pieces of the respiratory chain.

**ATP**

A molecule that cells use as an immediate source of energy.

**Respiratory chain, ETC, respiratory complex, and ATP synthase**

The respiratory chain, also called the electron transport chain or **ETC**, is a set of protein machines in mitochondria that helps convert energy from food. Each large protein machine is called a **complex**. ATP synthase, also called complex V, uses this process to make ATP.

**OXPHOS**

Short for oxidative phosphorylation. It includes the respiratory-chain complexes and ATP-production machinery. OXPHOS uses genes stored in both mtDNA and nuclear DNA.

**Nuclear OXPHOS structural-subunit genes**

Genes stored in nuclear DNA that make physical protein pieces of the OXPHOS machinery. They make most OXPHOS protein pieces.

**Mitochondrial translation**

The process mitochondria use to make proteins from their own genetic instructions.

**Mitonuclear relationship**

How expression from mtDNA and expression from nuclear-DNA mitochondrial genes move together. “Mito” refers to mitochondrial DNA and “nuclear” refers to nuclear DNA.

**Brain pathology**

Physical or molecular changes observed in brain tissue, such as amyloid plaques or tau tangles.

**Alzheimer disease, or AD**

A brain disease associated with memory loss, changes in thinking, and characteristic brain pathology.

**NCI**

“No cognitive impairment.” In this study, people in the NCI group are the main comparison group for people in the AD group. NCI does not mean that a brain is free of all pathology.

**Biological sample and donor**

A biological sample is material collected from a living organism. A **donor** is one person who contributed a brain sample. A study may measure thousands of nuclei from one donor, but those nuclei are not thousands of independent people. The donor is the independent sample.

**Neuron and cell type**

A neuron is a brain cell that communicates with other cells. A **cell type** is a class of cells with a particular job. This project focuses mainly on:

- astrocytes, which help support and regulate the environment around neurons;
- excitatory neurons, which usually increase the activity of connected neurons;
- inhibitory neurons, which usually reduce the activity of connected neurons.

**Cell context**

The cell type together with the planned donor group comparison and analysis setting.

**Recorded sex**

The female/male variable available in this dataset. It is used for the planned sex comparisons and is not the same thing as a person's gender identity.

**APOE group**

APOE is a gene with common forms called alleles. This project compares groups involving the ε2, ε3, and ε4 forms. APOE ε4 is a strong genetic risk factor for late-onset AD, while ε2 is often associated with lower risk. The exact study groups are defined in the main plan.

`APOE group` means the inherited APOE form carried by a donor. In the label `APOE–TUFM`, `APOE` instead refers to the APOE gene as a point in the gene network and may involve measured APOE RNA. These two uses are related, but they are not the same variable.

**Cohort**

A group of people studied together.

**Discovery cohort**

The group of people in whom a pattern was first found. A different cohort is needed for independent replication.

**ROSMAP**

The Religious Orders Study and Memory and Aging Project. ROSMAP is the main source of donor data used for the discovery analyses in this project.

### 1.2 Words used to combine many genes

**Gene set or gene module**

A list of genes that share a job. For example, an ATP-synthase module contains genes involved in the ATP-synthase machinery.

**Module score**

One number that summarizes the expression of many genes in a module. This helps us ask whether a biological program changes as a group instead of focusing on one gene.

**Candidate gene**

A gene suggested for further testing. “Candidate” means that evidence is still needed; it does not mean the gene has been proven important.

**Named partner or readout**

This phrase combines two related ideas.

A **named partner** is a specific gene paired with a candidate in the earlier computer-generated gene network, which is a map of estimated relationships among genes. The partner gives us a concrete gene-level prediction to test. For example, `TUFM` is the named partner in the `APOE–TUFM` hypothesis.

A **readout** is a measurement used as a sign of what may be happening in a biological process. Here, the measured RNA expression of `TUFM` is a readout of the `APOE–TUFM` hypothesis. The larger mitochondrial-translation gene module is a second, broader readout of that local process.

The same gene can therefore have both roles:

- it is the **partner** because the network paired it with the candidate;
- it is a **readout** because its measured RNA is used to test the prediction.

The word “partner” does **not** mean that the two proteins physically touch. The genes may be connected through one or more steps in the network rather than by one direct link. It also does not prove that the candidate controls the partner. The dash in `APOE–TUFM` means “a network-nominated relationship that we plan to test,” not a causal arrow.

Older project notes sometimes call these genes “mediators.” That label is too strong unless a cause-and-effect chain is tested directly. This guide therefore uses the safer phrase **named partner/readout**.

An **association** means that two measurements vary together in a repeatable way. It does not mean that one causes the other.

#### What “Primary convergence outcome” means

Break the phrase into three parts:

- **Primary:** this is the main version chosen before looking at the new candidate results. We do not switch to a different outcome because it gives a more exciting answer.
- **Convergence:** all candidate systems are tested against the same scientific yardstick. This lets us ask whether they point toward one measured change instead of merely being related to mitochondria in different ways.
- **Outcome:** the number being studied. Each eligible donor receives an outcome value within each planned cell context.

In this project, the Primary convergence outcome is the **NCI-reference mitonuclear residual**. That long name means:

> How much higher or lower a donor's observed mtDNA respiratory-expression score is than the value predicted from that donor's nuclear OXPHOS-expression score using the relationship estimated in the NCI comparison group.

It is calculated in four basic steps:

1. Calculate a nuclear OXPHOS score for each donor.
2. In NCI donors, learn how the mtDNA respiratory score is related to the nuclear OXPHOS score while accounting for the planned sex, APOE, age, and PMI information.
3. Use that NCI relationship to predict the mtDNA score expected for each donor.
4. Subtract the predicted mtDNA score from the observed mtDNA score.

```text
Primary convergence outcome
    = observed mtDNA respiratory score
      − NCI-reference predicted mtDNA respiratory score
```

For an invented example:

```text
predicted mtDNA score = 0.7
observed mtDNA score  = 0.2

outcome = 0.2 − 0.7 = −0.5
```

Here, `−0.5` means that the donor's mtDNA respiratory-expression score is lower than predicted from the NCI reference. A positive value means it is higher than predicted. A value near zero means it is close to the prediction.

Positive does not automatically mean healthy, and negative does not automatically mean harmful. The sign describes an RNA-expression relationship, not mitochondrial performance.

Why use one common outcome? Imagine testing three study methods with three completely different exams. Their scores would not show that all three methods improve the same skill. Giving all three the same exam creates a common yardstick. Here, the Primary convergence outcome is that common yardstick.

For the strict convergence claim:

- the outcome itself must show the planned, stable AD-by-sex or AD-by-APOE result;
- `APOE–TUFM`, `LAMTOR5–ATP5IF1`, and `GABARAPL2–CHCHD2/PARK7` must each be separately associated with this unchanged outcome;
- they must use the same frozen sex/APOE comparison and a compatible outcome direction;
- changing the outcome definition for one system would prevent a strict “same outcome” claim.

Important limits:

- This is an RNA-expression outcome. It does not directly measure oxygen consumption, ATP production, mitochondrial number, or cell health.
- This one outcome cannot pass C3 by itself. C3 requires agreement from at least two of the three planned measurements of the mtDNA–nuclear relationship.
- The same formula and gene rules are used across cell contexts, but the NCI reference is estimated separately within each cell context.
- An altered outcome made only as a gene-overlap sensitivity check is supporting evidence. It is not the unchanged Primary convergence outcome and cannot earn the strict convergence claim by itself.

#### The four different pieces of a candidate-system hypothesis

Do not treat these four pieces as if they were the same thing:

| Piece | Role in this analysis, explained simply | Examples |
|---|---|---|
| **Candidate gene** | The gene highlighted by the network as potentially important | `APOE`, `LAMTOR5`, `GABARAPL2` |
| **Named partner/readout** | The specific mitochondrial-related gene paired with that candidate and measured as a concrete prediction | `TUFM`, `ATP5IF1`, `CHCHD2`; `PARK7` is secondary |
| **Local gene module** | A larger group of genes representing the partner's biological process | Mitochondrial translation, ATP synthase, or mitochondrial stress/quality control |
| **Primary convergence outcome** | The common mtDNA-versus-nuclear OXPHOS measurement that all passing systems must connect to | How far mtDNA expression lies above or below the value predicted from nuclear OXPHOS using the NCI comparison group |

The exact candidate-to-partner mapping is:

| Candidate | Named partner/readout | Main local process | Important note |
|---|---|---|---|
| `APOE` | `TUFM` | Mitochondrial translation | `APOE` here is the gene/network node, not the donor's APOE genotype group |
| `LAMTOR5` | `ATP5IF1` | ATP synthase | The ATP-synthase module must be scored without `ATP5IF1` for the confirmation test |
| `GABARAPL2` | `CHCHD2` | Mitochondrial stress/quality control | `CHCHD2` is primary; `PARK7` is secondary and cannot rescue an unsupported `CHCHD2` result |

The logic is:

```text
network candidate
    associated with a named partner/readout
        associated with a local biological program
            associated with the shared mitochondrial outcome
```

Every line above means “an association to test.” It does not mean proven biological control.

#### Why not test only the candidate gene?

A network candidate does not have to show different average RNA abundance between groups. A gene that does show such a difference is later called a DEG. The candidate's average RNA might remain similar even if its network relationships are biologically interesting.

The named partner/readout makes the hypothesis more specific and easier to disprove. The local module then asks whether the partner is accompanied by a broader biological program rather than being one isolated gene result.

For a named system to receive donor-level support, we therefore want all of the following:

1. The named partner/readout has a compatible estimated direction in the planned cell context and sex/APOE comparison.
2. The local module also changes after the named partner/readout is removed from the module score.
3. The candidate gene has a planned relationship with the partner or local module. This is supporting evidence, not proof that the candidate controls them.
4. The candidate or another nonoverlapping network-neighborhood measurement—a score made from genes close to the candidate in the gene map—is associated with the Primary convergence outcome.
5. The candidate later beats fair comparisons with similar random gene lists and similarly connected network genes, and it remains stable after small network changes.

A significant named partner by itself is not enough. It could be an isolated gene result. A significant module by itself may support the biological program but not the named candidate–partner system.

#### Worked example: `LAMTOR5–ATP5IF1`

In this label:

- `LAMTOR5` is the network-nominated candidate;
- `ATP5IF1` is the named partner/readout;
- the ATP-synthase module represents the local biological program;
- the NCI-reference mitonuclear residual is the shared outcome.

The donor-level test asks:

1. Does `ATP5IF1` show a compatible effect in the planned neuronal comparison?
2. Does the rest of the ATP-synthase module show the pattern after `ATP5IF1` is removed from its score?
3. Is `LAMTOR5` related to `ATP5IF1` or the local program across donors after the planned adjustments?
4. Does a non-circular `LAMTOR5` or network-neighborhood measurement connect to the unchanged Primary convergence outcome?
5. Does the original network nomination survive fair network controls?

Possible interpretations are:

- If only `ATP5IF1` changes, report an interesting gene result, not a supported system.
- If the ATP-synthase module changes but `ATP5IF1` is incompatible, report the broader ATP-synthase result, not the full named system.
- If `LAMTOR5` is not a DEG, the system does not automatically fail; the partner, module, donor relationship, and network checks still determine support.
- If all required pieces pass, call it a **supported network-nominated system associated with the mitochondrial outcome**. Do not call it a proven regulator or cause.

#### RNA readout versus functional readout

The current project mainly has **RNA readouts**, such as `ATP5IF1` RNA abundance or an ATP-synthase RNA module score.

A **functional readout** would directly measure what mitochondria do, such as oxygen consumption or ATP production. The current RNA and network analyses cannot replace those functional measurements.

**Target-excluded module score**

A module score calculated after removing the named partner/readout gene. For example, the ATP-synthase score used to support `ATP5IF1` should be recalculated without `ATP5IF1`.

Why remove it? If `ATP5IF1` is part of its own score, a strong change in that one gene could make the whole score look supportive. Removing it asks whether the rest of the biological program also supports the result.

### 1.3 Words used for comparisons

**Postmortem interval, or PMI**

The time between a person's death and preservation of the brain tissue. It can affect RNA measurements, so the analysis accounts for it.

**AD effect**

The difference between AD donors and NCI donors after planned adjustments such as age and PMI.

**Modifier effect**

A direct test of whether the AD effect differs between groups.

For example:

```text
AD effect in females − AD effect in males
```

This is the correct way to ask whether the AD effect differs by sex.

It is **not** enough to say:

```text
significant in females, but not significant in males
```

Here, “significant” means that a result passed a chosen statistical threshold. Those two statements do not directly test whether females and males differ from each other.

**Cell-type difference**

A direct test of whether an effect in one cell type differs from the effect in another cell type. A result passing a statistical rule in astrocytes but missing it in neurons does not prove the cell types differ.

**Endpoint or outcome**

The exact measurement an analysis tries to explain. In this guide, the preferred shared endpoint is a measurement of the mtDNA–nuclear relationship.

**Statistical model**

A mathematical rule used to estimate a relationship while accounting for other recorded differences, such as age.

**NCI-reference relationship**

The relationship estimated in NCI donors. It provides a comparison pattern for asking whether an AD donor is above or below the value expected from that NCI reference.

**Residual**

The difference between what was observed and what a model predicted.

For example, suppose an NCI-based model predicts an mtDNA score of `0.7` for a donor based on that donor's nuclear OXPHOS score. If the observed mtDNA score is `0.2`, then:

```text
residual = observed − predicted
         = 0.2 − 0.7
         = −0.5
```

The negative residual means that the mtDNA signal was lower than expected from the NCI relationship. The numbers in this example are invented only to explain the idea.

**Shared endpoint**

One outcome that all three candidate systems are tested against. The preferred choice is the NCI-reference mitonuclear residual described above.

**Claim**

A scientific statement that we would like the evidence to support. `C1`, `C2`, and the other labels are short names for specific claims in this project.

**Frozen or prespecified**

Decided in writing before looking at the new result. Freezing the endpoint, gene lists, comparisons, and decision rules prevents us from changing the question just because another answer looks more exciting.

**Evidence matrix or scorecard**

A table that records which evidence is required for each claim and whether that evidence passed, failed, or remained uncertain.

**Gate**

A decision rule. A gate determines whether the evidence is strong enough to use certain words or to move a candidate into the next analysis round.

**Round**

A stage of the project. Later rounds are performed only when the required earlier evidence passes.

**Correlation**

A number describing how two measurements tend to change together. Correlation does not show that one measurement causes the other.

**Differentially expressed gene, or DEG**

A gene whose measured RNA abundance differs between compared groups. Being a DEG does not prove that the gene controls the change.

### 1.4 Words used to judge reliability

**Effect size**

How large an estimated difference or relationship is.

**Confidence interval, or CI**

A range of effect sizes reasonably consistent with the data. A wide interval means that the answer is uncertain.

**P value**

A number used to judge evidence against “no effect” for one test.

**q value**

A P value adjusted because many tests were performed. This adjustment reduces results that appear real only by chance. The main plan usually uses `q ≤ 0.05` as the statistical rule.

**Expected direction**

Whether a measurement is predicted to increase or decrease. The expected direction must be written down before looking at the new result.

**Minimum meaningful effect**

The smallest change considered large enough to matter scientifically. It is chosen before viewing the new results.

**Eligibility and nucleus-count threshold**

Eligibility means that a donor profile has enough required information to be used. A nucleus-count threshold is the minimum number of nuclei needed to build that donor's cell-context profile.

**RNA-quality measurement**

A recorded feature used to check whether technical sample quality might explain a result.

**Robust or stable result**

A result that remains similar under the planned reasonable repeat analyses, such as leaving out one donor or changing a quality threshold.

**Bootstrap**

Repeat the analysis many times using newly selected sets of donors from the original data, with repeated selection allowed. This repeated selection is called resampling. If an estimated effect repeatedly keeps the same direction, it is more stable.

**Leave-one-donor-out test**

Repeat the analysis while removing one donor at a time. If removing one person reverses the answer, the result is fragile.

**Sensitivity test**

Repeat an analysis using another reasonable quality threshold or scoring method. A trustworthy conclusion should not disappear after a small, sensible change.

**Independent replication**

Repeat the planned test in a different group of people. Repeating several analyses in the same people is not independent replication.

**Random seed**

A saved number that makes a computer's random resampling or simulation reproducible.

### 1.5 Network words

**Gene network**

A mathematical map in which genes are points and estimated relationships between genes are lines.

**Network node, link, and edge**

A gene shown as a point is a **node**. A line between two nodes is a **link** or **edge**. A directed edge has a drawn direction, but that direction is still a network estimate and not proof of cause.

**Network connectedness or degree**

How many network links a gene has. In a directed network, incoming and outgoing links can be counted separately.

**Network proximity and neighborhood**

Proximity describes how few links separate two genes. A candidate's neighborhood is the set of genes found within a chosen number of links from it.

**Network rank**

A candidate's ordered position after all candidates are sorted from strongest to weakest by a chosen network result.

**Network module**

A cluster of genes that are close or strongly connected in a network. This is not automatically the same as a biological gene set defined from known functions.

**Network-nominated candidate**

A gene highlighted by a network analysis as being unusually close to, or connected with, a group of genes of interest. “Nominated” means suggested for further testing. It does not mean proven.

**Candidate system**

In this guide, a candidate system contains:

- a network-nominated candidate;
- a named mitochondrial partner or readout;
- a local biological module;
- the planned cell type and sex/APOE comparison.

The dash in a name such as `APOE–TUFM` means “a network-nominated relationship to test.” It does not automatically mean that the two proteins physically touch or that the first gene controls the second.

**Query genes**

The genes supplied to a network search as the biological pattern of interest.

**KDA**

Short for key-driver analysis. It asks whether a candidate gene is unusually close to many query genes in a network.

**Hub**

A network gene with many connections. A hub can look important simply because it has many chances to be close to other genes.

**Null comparison**

A fair chance comparison. The real result is compared with many artificial examples that have similar basic features.

This project needs two different null comparisons:

1. **Query-matched null:** compare the real query with random gene lists that have similar size, expression, detection, and network properties.
2. **Topology-matched null:** compare the candidate with other genes having similar numbers and patterns of network connections. “Topology” means the shape of the network connections.

**Alternative network**

A second network built with a different method or data source. Support in a second network reduces the chance that the result is caused only by the first network's construction.

**Convergence**

Several separately supported systems connecting to the same endpoint. If only one system passes, there is no cross-system convergence.

**Association**

Two measurements vary together in a repeatable way. Association alone does not show that one causes the other.

**Causation**

Changing one thing directly produces a change in another. Causation usually requires a controlled experiment, such as changing a candidate gene in cells and measuring the result.

**Perturbation experiment**

A controlled experiment that deliberately increases, decreases, or otherwise changes a candidate gene or protein.

**Rescue experiment**

An experiment that asks whether restoring a predicted gene or process reverses the effect of a perturbation.

---

## 2. The short answer and the whole idea in one picture

This guide answers two questions:

1. What evidence would show that the three network-nominated systems point to the same biological change?
2. Does one of those systems need to explain Claims C1, C2, and C3?

The short answers are:

- C1 must pass for sex/APOE wording, C3 must pass for mitonuclear wording, and C2 must pass only if we say the result is cell-type-specific.
- The three gene systems are possible biological programs associated with that pattern. They cannot rescue whichever core claim failed.
- No single gene system needs to explain all of C1, C2, and C3.
- To say that **three systems converge on the same change**, every one of the three must be evaluated separately and connect to one clearly defined mitochondrial measurement. Finding all three in a mitochondrial network search is not enough.
- These RNA and network analyses can show a reliable **association**. They cannot show that a gene system causes the mitochondrial change. A cause-and-effect claim needs laboratory experiments.

Think of the project as having two levels.

```text
LEVEL A: First establish the biological event

    C1: Who shows a different AD effect?
        Sex and/or APOE groups

    C2: Where is the effect different?
        Astrocytes, excitatory neurons, or inhibitory neurons

    C3: What mitochondrial relationship changes?
        The relationship between mtDNA-encoded respiratory-chain genes
        and nuclear-DNA-encoded OXPHOS structural-subunit genes

                         ↓

            One clearly defined shared outcome

                         ↓

LEVEL B: Then test possible systems connected to that event

    APOE–TUFM in astrocytes -------------------\
                                                \
    LAMTOR5–ATP5IF1 in neurons -----------------[ same shared outcome ]
                                                /
    GABARAPL2–CHCHD2/PARK7 --------------------/
    in excitatory neurons

    Every line means “tested association.”
    No line is a causal arrow.
```

Level A asks whether the event exists. Level B asks whether particular gene systems are reliably associated with it.

The downward arrow shows analysis order, not biological cause. This order matters: a network result cannot be used to manufacture the biological event that it is supposed to explain.

---

## 3. What Claims C1, C2, and C3 mean

Claims C1–C3 describe the main biological pattern. They are not candidate-gene claims.

| Claim | Simple question | What a passing result would allow us to say |
|---|---|---|
| C1 | **Who?** Does sex or APOE change the AD respiratory effect? | The AD-related respiratory change is modified by sex and/or APOE. |
| C2 | **Where?** Is the modifier effect truly different between cell types? | The modifier effect is different between named cell types. |
| C3 | **What?** Does AD change the NCI-reference relationship between mtDNA-encoded respiratory-chain expression and nuclear-encoded OXPHOS structural-subunit expression? | There is an AD-related mitonuclear expression change. |

These claims are related, but they are not identical.

- C1 can pass while C2 fails. We could then say there is a sex/APOE-modified result, but not that it is cell-type-specific.
- C1 can pass while C3 fails. We might have a nuclear OXPHOS result, but not a proven mitonuclear result.
- C3 can pass while C1 fails. We might have a general AD-related mitonuclear result, but not evidence that sex or APOE modifies it.

A **structural-subunit gene** makes a physical piece of an OXPHOS protein complex. This definition keeps the nuclear side of C3 focused instead of mixing it with every gene that has any mitochondrial job.

C3 is not allowed to pass because one residual test looks interesting. The full Gate 2 rule from the main plan is:

- calculate all three planned measurements of the mtDNA–nuclear relationship:
  1. the difference between the NCI-scaled mtDNA and nuclear scores;
  2. the NCI-reference residual explained earlier;
  3. whether the strength of the mtDNA-versus-nuclear relationship changes between the planned groups;
- require at least two of the three to point in a compatible direction and have `q ≤ 0.05`;
- require one of those two to be the NCI-reference residual or the change in how strongly the mtDNA and nuclear scores move together;
- require the planned alternative scoring and RNA-quality checks to agree.

If the final claim says the mitonuclear change is modified by sex or APOE, C3 must also pass the relevant direct modifier comparison. A general AD effect alone cannot support sex/APOE wording.

### Does one candidate system need to explain all three claims?

**No.**

C1–C3 must be tested using the full donor data and the prespecified respiratory measurements. They test separate parts of the event before candidate systems are considered. The final sentence can use only the core clauses whose tests passed.

The candidate systems have a different job. They ask whether a particular local gene program, in a particular cell context, is reliably connected to that event.

Another way to remember this is:

```text
C1–C3: Is the event real, who shows it, and where does it differ?

Candidate systems: Which specific biological systems are associated with it?
```

One candidate might be most relevant in astrocytes. Another might be most relevant in excitatory neurons. It would be unreasonable to require each candidate to explain every cell type and every sex/APOE difference.

However, if a candidate is included in the final central story, its evidence must match:

- its planned cell context;
- its planned sex/APOE comparison;
- its predicted local biological process;
- the same shared respiratory endpoint used by the other named systems.

For the strongest phrase—“the same sex/APOE-resolved change”—all named systems must use the same frozen modifier comparison and biologically compatible directions. If different candidates pass only in different sex/APOE comparisons, say that they are **related to respiratory biology in different contexts**. Do not call those results the same sex/APOE-resolved change.

The word **explain** should still be avoided. These analyses can show that a candidate system is associated with the event. They cannot show that it produced the event.

---

## 4. What are the three candidate systems?

The three systems came from earlier network analysis. They are hypotheses to test, not established mechanisms.

| Candidate system | Main cell context | Local process to test | Named mitochondrial readout | Shared outcome it must connect to |
|---|---|---|---|---|
| `APOE–TUFM` | Astrocytes | Mitochondrial protein production | `TUFM` and a mitochondrial-translation module without `TUFM` | Frozen mitonuclear respiratory endpoint |
| `LAMTOR5–ATP5IF1` | Primarily excitatory neurons | ATP-synthase program | `ATP5IF1` and an ATP-synthase module without `ATP5IF1` | Frozen mitonuclear respiratory endpoint |
| `GABARAPL2–CHCHD2`/`PARK7` | Excitatory neurons | Mitochondrial stress/quality-control program | `CHCHD2` as primary; `PARK7` as secondary; a module without both genes | Frozen mitonuclear respiratory endpoint |

Some gene-specific background:

- `APOE` helps transport fats and cholesterol. Common APOE forms are also related to AD risk.
- `TUFM` helps mitochondria make proteins from mitochondrial genetic instructions.
- `LAMTOR5` is part of cellular machinery involved in sensing nutrients and relaying signals.
- `ATP5IF1` is related to control of ATP synthase, the machinery that makes ATP.
- `CHCHD2` has mitochondrial roles related to respiration and stress responses.
- `PARK7`, also called DJ-1, is related to cellular stress protection. It is secondary in this plan and cannot rescue an unsupported `CHCHD2` result.
- `GABARAPL2` is related to cell recycling pathways, including processes connected to quality control of structures inside cells.

These descriptions explain why the systems are biologically interesting. They do not prove that the network direction is correct.

---

## 5. What does “the same biological change” mean?

This phrase can mean three very different things. We must choose the strongest meaning that the data actually support.

### Meaning 1: all three are vaguely related to mitochondria

This is weak evidence.

Many genes are related to mitochondria. Also, the original KDA used mitochondrial genes as the query. It is therefore not surprising that the nominated results have mitochondrial connections.

We should **not** use “three systems converge on the same biological change” based only on this evidence.

### Meaning 2: all three relate to respiratory biology or OXPHOS

This is more focused, but it is still broad.

If the systems involve different comparisons, different directions, or different outcome measurements, a safe sentence would be:

> Three candidate systems are connected to mitochondrial respiratory biology in different cell contexts.

That is not the same as showing that they all point to one measured change.

### Meaning 3: all three are separately evaluated against one frozen donor-level endpoint definition

This is the strongest computational meaning.

The recommended bridge outcome is:

> How far each donor's mtDNA respiratory score is above or below the value predicted from that donor's nuclear OXPHOS score, using the relationship estimated in NCI donors.

This is called the **NCI-reference mitonuclear residual**. The same formula and gene rules are used in every planned cell context, but a separate NCI reference is fitted within each cell context.

It must be chosen before checking which candidate gives the nicest result. The gene list, cell contexts, comparisons, direction rules, and quality rules must also be written down first.

The residual is the shared **bridge outcome**. It does not replace the full C3 test. C3 still needs two of its three planned mitonuclear measurements to pass the Gate 2 rules. In addition, the residual contrast itself must pass its prespecified rule before it can serve as the convergence bridge.

If all three systems separately connect to this bridge outcome, survive stability checks, and beat fair network controls, then it may be reasonable to say that they converge on the same **transcriptional** endpoint.

There is one further rule for sex/APOE wording. All named systems must use the same frozen modifier comparison and a compatible endpoint direction. If the systems pass different sex/APOE comparisons, they share a **type of measurement**, not one sex/APOE-resolved change.

“Transcriptional” is important. The endpoint is made from RNA measurements. It does not directly measure mitochondrial respiration or ATP production.

---

## 6. The evidence chain needed for each system

Use the same evidence chain for all three systems. Do not give one candidate an easier rule because it looks interesting.

```text
relevant core claim passes
    → candidate's local phenotype passes
    → non-circular donor bridge passes
    → candidate's network checks pass
    → candidate counts toward the convergence sentence
```

Failure of one candidate does not invalidate C1–C3. However, failure of the relevant C1 or C3 clause prevents the proposed convergence sentence even if the network plots look strong.

Two phrases used below have precise meanings:

- **local phenotype:** the predicted named-partner and gene-module expression pattern in the planned cell context;
- **non-circular bridge:** a comparison in which the two measurements do not reuse the same genes, so the answer is not partly built into the calculation.

Keep these two outcomes separate:

| Label used in this guide | What it is | Can it earn the strict convergence sentence? |
|---|---|---|
| **Primary convergence outcome** | The unchanged frozen NCI-reference residual used for every system | Yes; it is required |
| **Optional non-overlap sensitivity outcome** | An altered bridge-only residual, such as one that leaves ATP-synthase genes out of the nuclear score | No; it is supporting evidence only |

### Evidence 1. The core mitochondrial event exists without using the candidates

First test C1–C3 using donor-level data.

Why this matters: if the shared mitonuclear event is not supported, candidate systems cannot be said to converge on it.

Minimum requirement for the full claim:

- C1 passes for the exact sex/APOE comparison used in the final convergence sentence. Five donors in every required group permits estimation, but a headline comparison should have at least 10 per group. A below-10 comparison, especially male ε2, remains provisional unless the same direct modifier is replicated in an independent cohort;
- C3 passes its full Gate 2 rule, and the chosen residual bridge passes for that same comparison;
- C2 passes only if the final sentence uses “cell-type-specific.”

If C2 does not pass, the candidate systems may still be discussed in their measured cell contexts. The wording should be “cell-context-resolved,” not “cell-type-specific.”

### Evidence 2. The system has the predicted local pattern

Each candidate must show the expected local biological pattern in the correct cell context.

For example, `LAMTOR5–ATP5IF1` requires evidence about:

- `ATP5IF1` expression;
- the ATP-synthase module after removing `ATP5IF1`;
- the planned AD-by-sex or AD-by-APOE comparison;
- the planned neuronal cell context.

The same logic applies to the other two systems.

Why this matters: the target-excluded module shows that support does not come from only one highlighted gene.

### Evidence 3. The local program and shared outcome match the same planned group comparison

First, test the two measurements separately:

1. Does the target-excluded local program show the frozen AD-by-sex or AD-by-APOE comparison?
2. Does the residual bridge outcome show that same comparison in a biologically compatible direction?

This is the primary evidence that both results match the same group pattern. A correlation alone does not test the sex/APOE modifier.

For `LAMTOR5–ATP5IF1`, ATP-synthase genes are part of nuclear OXPHOS. Therefore, the matching group pattern is a consistency check, not an independent confirmation. The separate nonoverlapping bridge in Evidence 4 is especially important for this system.

### Evidence 4. Prevent the two compared measurements from reusing the same genes

If two scores contain some of the same genes, they can correlate automatically. That would be **circular evidence**, meaning that part of the answer was built into the test itself.

Before viewing the new candidate results:

1. List the genes in the shared outcome and every local module.
2. Count the overlap for each candidate system.
3. Remove the named partner/readout from its own local-program score.
4. Choose and freeze a bridge predictor that does not contain genes from the shared outcome. The first choices are the candidate gene itself or a prespecified upstream neighborhood score with adequate gene coverage.
5. Check that enough genes remain to represent the planned program reliably.
6. Mark the bridge `not_testable` if no meaningful nonoverlapping predictor can be built.

Do **not** automatically remove all nuclear OXPHOS genes from the ATP-synthase module. ATP synthase is OXPHOS complex V, so that rule could destroy the module.

If a separate program score is scientifically required for `LAMTOR5–ATP5IF1`, freeze one workable non-circular solution before outcome testing. For example, keep the full endpoint for C3 but build the **Optional non-overlap sensitivity outcome** by leaving ATP-synthase genes out of its nuclear score. Report how many genes remain and do not pretend it is numerically identical to the full C3 endpoint.

For the strict phrase “the same endpoint,” the **Primary convergence outcome** must remain unchanged. The optional sensitivity outcome cannot by itself earn the convergence sentence.

### Evidence 5. A separate donor-level association supports the bridge

For each donor, calculate:

1. a candidate or upstream-program measurement that does not reuse genes from the shared outcome;
2. the unchanged **Primary convergence outcome**.

Then ask whether the two measurements tend to move together in the planned cell context after accounting for:

- AD/NCI, sex, and APOE group;
- age;
- PMI;
- planned RNA-quality measurements.

This adjusted association asks whether the two measurements are related among donors even after differences between the AD, sex, and APOE groups have been accounted for. It is supporting evidence. It does not itself test the AD-by-sex or AD-by-APOE modifier.

Do not put mitochondrial-read fraction into the primary model automatically because the outcome itself contains mitochondrial RNA. Add it only as a prespecified sensitivity check. Add another technical quality measurement to the primary model only if it is available for nearly all required donors and does not nearly duplicate group membership or another model variable.

If the scientific question specifically asks whether this donor-level association changes between groups, freeze and test an additional `local measurement × group` comparison. Do not add it after seeing the result.

Also test the candidate gene's relationship with its named partner or target-excluded local program. This keeps the candidate itself in the evidence chain. The local-program score alone should not be mislabeled as a direct measurement of `APOE`, `LAMTOR5`, or `GABARAPL2`.

### Evidence 6. The donor-level bridge is stable

For each candidate system:

- calculate the relationship size and its 95% CI;
- adjust for every primary bridge test that was actually run and report the q value;
- repeat with at least 1,000 donor bootstraps;
- repeat after leaving out each donor one at a time;
- repeat with the planned alternative module score;
- repeat under the planned RNA-quality and nucleus-count rules.

A useful planned rule is:

- `q ≤ 0.05` for each named system;
- the standardized relationship size reaches the minimum meaningful size chosen before testing;
- the 95% CI excludes zero in the direction chosen before looking at the result, or it passes another minimum-meaningful-effect rule frozen in the main plan;
- at least 80% of bootstrap repeats keep that direction;
- no leave-one-donor-out run reverses the result;
- reasonable quality and scoring changes keep the conclusion.

Bootstrap whole donors, never individual nuclei. A stable direction with a very wide CI is still inconclusive.

In every bootstrap and leave-one-donor-out repeat, recalculate the NCI averages and variation, refit the NCI reference model, rebuild the residual, and rebuild the bridge measurement. Freeze the formulas and gene lists, not the original fitted numbers. If an NCI donor is left out, that donor must be excluded from both the NCI scaling and the NCI reference fit.

A **standardized relationship size**, or standardized slope, tells us how much the outcome changes, in comparable units, when the bridge measurement changes by one comparable unit. Its minimum meaningful size must be written down before viewing the results.

Correcting only three tests is valid only if there is exactly one primary cell context, comparison, outcome, and bridge measurement per system. If more primary versions are tested, all candidate × context × comparison × outcome tests must be corrected together. Secondary analyses must be labeled secondary.

The expected relationship direction must be chosen before viewing the results. If there is no defensible expected direction, use a two-sided test, which allows either direction, and do not invent a preferred direction afterward.

### Evidence 7. The network result beats fair chance comparisons

Each candidate must pass its own Round 2 network tests:

1. Remove query genes from possible driver genes so a query cannot nominate itself.
2. Compare against at least 1,000 random query lists matched for list size, RNA expression, how often the genes were detected, mitochondrial composition, mtDNA fraction, network connectedness, and tested-gene coverage.
3. Compare against at least 1,000 genes matched for their incoming and outgoing network links, overall connectedness, neighborhood sizes, expression, detection, and tested-gene coverage.
4. Slightly change network edges and check that the candidate remains highly ranked.
5. Look for supporting proximity or module membership in an alternative donor-level network.

Why this matters: a candidate may be nominated because the query was mitochondrial or because the candidate is a large hub. These controls test those two problems separately.

The alternative donor-level network should be built by comparing expression patterns across donors, treating donors rather than nuclei as the independent samples. Agreement supports robustness to network construction. It still does not prove the direction of biological control.

### Evidence 8. The systems remain distinguishable after shared genes are removed

After removing the KDA query genes and the genes used in the shared endpoint, inspect the remaining network neighborhoods.

The three systems should retain their different local context:

- mitochondrial translation for `APOE–TUFM`;
- `ATP5IF1` and its upstream signaling or regulatory context for `LAMTOR5–ATP5IF1` after shared ATP-synthase structural genes are removed;
- stress or quality control for `GABARAPL2–CHCHD2/PARK7`.

Also compare how many remaining neighborhood genes are shared between the systems. Compare that overlap with size- and connectedness-matched candidate pairs. The observed overlap must not exceed the 95th percentile of matched overlaps. In plain language, it must not be among the largest 5% of overlaps seen for fair comparison pairs.

If the three “systems” mostly contain the same remaining genes, they may be three labels for one recurrent network module. A **network module** is a cluster of genes that are close or strongly connected in the network. Report one shared network module instead of claiming three distinct candidate-associated programs.

### Evidence 9. The result is checked outside the discovery data

Keep three kinds of evidence separate:

- RNA from different donors is **independent RNA replication**;
- protein from different donors is independent support from a different kind of measurement;
- protein from the same ROSMAP donors is same-cohort support from a different kind of measurement.

Independent RNA data test whether the shared endpoint and candidate links appear in other people. Protein data test a different biological layer. A protein that was not measured must be labeled `not_measured`, not failed.

---

## 7. What exactly should be calculated for the donor-level bridge?

This section gives a concrete procedure. It is a **proposed strengthening** of the main plan, not yet one of the main plan's official Gate 3 rules. If this strengthening is accepted, it must be added to the main plan, scheduled before the stability task, and included in the locked decision table before it is run.

### 7.1 Inputs

Use:

- one RNA-expression profile per donor and cell context;
- donor AD/NCI, sex, APOE, age, and PMI information;
- planned RNA-quality measurements;
- the frozen mtDNA respiratory gene list;
- the frozen nuclear OXPHOS gene list;
- the frozen local module for each candidate system;
- the frozen cell context and direct sex/APOE comparison for each system;
- a new small rules table, called a **manifest**, that lists the single primary bridge test for each system.

The manifest should be saved before outcome testing:

```text
results/<version>/candidates/candidate_common_endpoint_manifest.tsv
```

### 7.2 Build the Primary convergence outcome

1. Within each cell context, use NCI donors to put the mtDNA ETC and nuclear OXPHOS scores onto comparable scales. Do this by subtracting the NCI average and dividing by the amount of donor-to-donor variation in NCI. This scaling step is called **standardization**.
2. Within that cell context, use NCI donors to fit this reference:

   ```text
   mtDNA ETC score
       estimated from nuclear OXPHOS score, sex, APOE, age, and PMI
   ```

3. Freeze the fitted reference for scoring the main dataset. Do not refit it separately in AD groups.
4. Use it to predict each eligible donor's mtDNA ETC score.
5. Subtract the predicted score from the observed score.
6. For NCI donors, repeat both the NCI scaling and reference fitting while leaving that donor out. This checks that an NCI donor does not help set the scale or predict itself.
7. Save the residual for every donor and eligible cell context.
8. During every donor bootstrap or leave-one-donor-out stability repeat, recalculate the NCI scale and refit the NCI reference inside that repeat. The formula and gene lists stay frozen; the fitted numbers do not.

Output:

```text
results/<version>/mitonuclear/donor_mitonuclear_scores.tsv.gz
```

Each row should include donor ID, cell context, observed mtDNA score, nuclear OXPHOS score, predicted mtDNA score, residual, group information, quality fields, reference-sample count, and whether the prediction came from the main or leave-one-out reference.

### 7.3 Build a non-circular bridge measurement for each system

1. Keep the target-excluded local module as the candidate's local phenotype test.
2. Create a gene-overlap table comparing that module with the full shared outcome.
3. Choose the primary bridge measurement before outcome testing. Prefer:
   - expression of the candidate gene itself; or
   - a prespecified upstream network-neighborhood score that shares no genes with the outcome.
4. If a local-program score must be used, remove overlapping genes only after checking that the remaining genes still represent the program reliably.
5. For the ATP-synthase system, do not empty the module by removing all complex-V genes. Use a prespecified disjoint candidate/upstream score, or create and clearly label the **Optional non-overlap sensitivity outcome** using a nuclear reference that excludes complex V.
6. Record all included and excluded genes, the reason for exclusion, the number and fraction remaining, and a reliability check.
7. If no scientifically meaningful nonoverlapping measurement remains, label the bridge `not_testable`.
8. Calculate one bridge measurement per donor in the planned cell context.

Outputs:

```text
results/<version>/candidates/candidate_endpoint_overlap_audit.tsv
results/<version>/candidates/donor_candidate_bridge_measurements.tsv.gz
```

The first file makes it possible to check that the analysis was not circular or biologically emptied by gene removal.

### 7.4 Test the bridge

For each system, save two different tests. They answer different questions.

**Primary pattern-matching test**

Check whether the target-excluded local program and the **Primary convergence outcome** both show the same frozen direct AD-by-sex or AD-by-APOE comparison in compatible directions.

**Supporting donor-association test**

Estimate this relationship:

```text
Primary convergence outcome
    associated with the nonoverlapping candidate or upstream measurement
    while accounting for biological group, age, PMI,
    and preapproved, sufficiently complete technical-quality measurements
```

This asks whether the two donor measurements are related after recorded group differences are accounted for. It does not test the sex/APOE modifier. If a group-specific association is a primary question, write down and test that additional comparison in advance.

Repeat the bridge with mitochondrial-read fraction only as a sensitivity analysis, not as an automatic primary adjustment.

Save:

- system name;
- exact statistical model and exact relationship being tested;
- donor count;
- donor IDs and counts in every required group;
- cell context;
- planned comparison;
- score-standardization method;
- genes before and after exclusions and post-exclusion reliability;
- primary pattern-match status;
- relationship size;
- 95% CI;
- P value;
- q value and the complete group of primary tests corrected together;
- expected direction chosen before testing;
- observed direction;
- bootstrap stability;
- leave-one-donor-out stability;
- result under each quality sensitivity;
- software version, input version, and random seed.

Output:

```text
results/<version>/candidates/candidate_common_endpoint_results.tsv
```

### 7.5 Important limit of this calculation

Even a stable association does not prove that the candidate system causes the endpoint. Both measurements could respond to another process that was not measured.

---

## 8. How the evidence matrix should show the connection

The main plan already has separate rows for C1–C9. The table below proposes a clearer display. It splits the network decision by candidate and adds a derived convergence summary. These display changes are not official until the main plan is updated too.

| Role | Claim | Plain-language question | Required evidence | Decision rule |
|---|---|---|---|---|
| Core event | C1 | Does sex or APOE change the AD respiratory effect? | Direct donor-level modifier and stability tests | Gate 1A |
| Core event | C2 | Does that modifier differ between cell types? | Direct between-cell comparison and stability tests | Gate 1B |
| Core event | C3 | Does the mtDNA–nuclear relationship change? | Full three-endpoint Gate 2 test; residual bridge must also pass for convergence | Gate 2 |
| Candidate 1 phenotype | C4 | Does `APOE–TUFM` show its predicted astrocyte pattern? | Named partner/readout, target-excluded translation module, correct context and comparison | Gate 3A |
| Candidate 2 phenotype | C5 | Does `LAMTOR5–ATP5IF1` show its predicted neuronal pattern? | Named partner/readout, target-excluded ATP-synthase module, correct context and comparison | Gate 3B |
| Candidate 3 phenotype | C6 | Does `GABARAPL2–CHCHD2/PARK7` show its predicted excitatory-neuron pattern? | Primary `CHCHD2`, target-excluded quality-control module, correct context and comparison | Gate 3C |
| Candidate 1 network | C7a | Does `APOE–TUFM` beat fair network controls? | Both null comparisons, network stability, alternative network | Candidate-specific Gate 4 |
| Candidate 2 network | C7b | Does `LAMTOR5–ATP5IF1` beat fair network controls? | Both null comparisons, network stability, alternative network | Candidate-specific Gate 4 |
| Candidate 3 network | C7c | Does `GABARAPL2–CHCHD2/PARK7` beat fair network controls? | Both null comparisons, network stability, alternative network | Candidate-specific Gate 4 |
| Independent RNA | C8 | Does the frozen endpoint appear in a different group of donors? | Frozen independent-cohort RNA test | Gate 5A |
| Protein support | C9 | Does a passing program receive support from protein measurements? | Frozen protein test with measurement coverage reported | Gate 5B |
| Derived summary | Cross-system convergence | How many separately supported systems connect to the same frozen endpoint definition and modifier comparison? | Relevant core gates, candidate phenotype gates, donor bridge, and candidate network gates | Count only systems that pass every required part |

For each candidate, the matrix should also contain these columns:

```text
system
exact_cell_context
planned_modifier_comparison
local_process
primary_convergence_outcome
optional_sensitivity_outcome
phenotype_status
donor_bridge_status
network_status
external_RNA_status
protein_status
contributes_to_convergence
```

`contributes_to_convergence` can be `yes` only when all required boxes for that candidate pass. One very strong candidate cannot compensate for two failed candidates.

For each Gate 3 candidate phenotype, require the exact rules from the main plan:

- the target-excluded local module has `q ≤ 0.05`;
- its 95% CI meets the minimum meaningful-effect rule chosen in advance;
- at least 80% of donor bootstraps keep the direction;
- no leave-one-donor-out result reverses the direction;
- alternative scoring and RNA-quality checks agree;
- the named partner/readout has a compatible direction and either candidate-family `q ≤ 0.10` or a CI that rules out a meaningful opposite effect;
- at least five donors are present in every needed group, while any below-10 ε2 result remains provisional.

For each candidate-specific Gate 4 network decision, require:

- at least 10 usable query genes;
- the exact tested-gene and network background;
- fixed network layers 1, 2, and 3 with correction for checking multiple layers;
- corrected KDA `q ≤ 0.05`;
- `q ≤ 0.05` under both matched chance comparisons;
- a result more extreme than at least 95% of both matched chance sets;
- top-10% candidate rank in at least 80% of small network-change repeats;
- alternative-network support at `q ≤ 0.05`, preserved in at least 80% of donor bootstraps.

The status should distinguish:

- `pass`: the planned evidence is present;
- `fail`: the estimate is precise enough and the planned evidence is absent;
- `inconclusive`: the uncertainty is too large to decide;
- `not_testable`: the needed data are unavailable;
- `not_started`: the analysis has not been run.

“Not measured” must never be changed into “failed.”

---

## 9. What counts as enough evidence for the exact sentence?

### To say “three systems converge on the same mitonuclear transcriptional change”

All of the following must be true:

1. C1 passes for the modifier language used in the sentence.
2. C3 passes for the shared mitonuclear endpoint.
3. C2 passes if the sentence says “cell-type-specific.”
4. C4, C5, and C6 each pass separately.
5. Each system has a stable, non-circular donor-level bridge using the unchanged Primary convergence outcome, the same modifier comparison, and a compatible endpoint direction.
6. C7a, C7b, and C7c each pass their own network controls.
7. The three remaining network neighborhoods retain distinguishable local programs after shared genes are removed.
8. The number of systems named in the sentence equals the number that passed every required step.
9. For the strongest version, the shared endpoint is supported in independent RNA data, with candidate-specific external evidence where the needed measurements exist.

Do not combine the three candidates into one summary test that lets one excellent candidate hide two unsupported candidates.

### If two systems pass

Say:

> Two candidate systems—[name them]—converge on the frozen mitonuclear transcriptional endpoint.

Do not keep the third system in the central claim.

### If one system passes

Say:

> [System name] is a robust network-nominated candidate associated with the mitonuclear transcriptional endpoint in [cell context].

Do not use “multiple systems converge.”

### If no system passes

C1–C3 may still provide the main result. Say that the original network candidates remained exploratory and did not pass confirmation.

### If C2 fails but other evidence passes

Use “cell-context-resolved.” Do not use “cell-type-specific.”

### If C3 fails but nuclear OXPHOS passes

Do not use “mitonuclear.” The project may support a narrower statement about nuclear respiratory transcription. The candidate tests must then be interpreted against that narrower endpoint, with the change documented before running a new confirmation analysis.

### If a candidate passes but the core endpoint fails

The candidate cannot support the proposed convergence claim. At most, it is an exploratory clue for a different biological question.

---

## 10. Results that look interesting but are not enough

None of the following proves three-system convergence:

- all three names appear in one network plot;
- all three KDA results use mitochondrial query genes;
- all three have an unadjusted, or “nominal,” P value below `0.05` without correction for testing many questions;
- a candidate is a DEG;
- a result is significant in one sex/APOE group but not another;
- the candidates correlate with mitochondrial scores that reuse some of the same genes;
- one candidate is strong and a combined test across all three is significant;
- several analyses agree but use the same donors and the same network;
- network arrows point from a candidate toward a mitochondrial gene;
- the result appears only after changing the endpoint or direction after viewing the data.

---

## 11. What can and cannot be concluded at each round?

| Round completed | Strongest reasonable statement if all planned tests pass | What still cannot be claimed |
|---|---|---|
| Round 1 | The passing candidate systems show stable donor-level patterns compatible with the same frozen respiratory endpoint definition and comparison. | They have not yet passed the matched chance and network-stability checks. |
| Round 2 | The passing, distinguishable network-nominated systems converge on the same transcriptional endpoint after the matched chance and network-stability checks. | They do not yet have independent replication and are not causal. |
| Round 3 | The frozen endpoint is independently replicated; name only candidate systems with appropriate external or protein support. | Association still does not prove causation or mitochondrial function. |
| Round 4 laboratory work | Carefully designed perturbation and rescue experiments may support a causal mechanism. | The exact causal sentence depends on the experiment and direct functional measurements. |

### Why laboratory work is needed for causal words

RNA data show transcript abundance. Network data show estimated relationships. To say that a candidate **drives**, **regulates**, or **causes** mitochondrial dysfunction, we would need to:

1. change the candidate gene in an appropriate cell model;
2. measure the named partner/readout and local module;
3. measure the shared respiratory phenotype;
4. directly measure mitochondrial function, such as oxygen consumption or ATP production;
5. perform a rescue experiment when possible.

A **rescue experiment** asks whether restoring the predicted partner/readout or pathway reverses the effect caused by changing the candidate.

---

## 12. Evidence-summary figure specification

Create one evidence figure with three parts.

### Panel A: Is the core event supported?

Show three boxes:

```text
C1: sex/APOE modifier       pass / fail / inconclusive
C2: cell-type difference   pass / fail / inconclusive
C3: mitonuclear endpoint   pass / fail / inconclusive
```

Include one main effect size and CI in each box.

### Panel B: Does each candidate complete the evidence chain?

Use one row per candidate:

| System | Cell context | Frozen modifier and endpoint direction | Local module and named readout | Donor bridge | Network controls | Contributes? |
|---|---|---|---|---|---|---|
| `APOE–TUFM` | Astrocytes | planned comparison/direction | status | status | status | yes/no/inconclusive |
| `LAMTOR5–ATP5IF1` | Neurons | planned comparison/direction | status | status | status | yes/no/inconclusive |
| `GABARAPL2–CHCHD2/PARK7` | Excitatory neurons | planned comparison/direction | status | status | status | yes/no/inconclusive |

Show failed and inconclusive boxes in gray or another clear color. Do not hide them.

Use lines labeled “associated with” or “network-nominated link.” Do not use causal arrows.

### Panel C: Is there evidence outside the discovery analysis?

Show separate columns for:

- independent RNA replication;
- protein support;
- not measured.

“Not measured” should look different from “measured but unsupported.”

---

## 13. Practical checklist

Do these steps in this order.

### Before looking at new candidate results

- [ ] Freeze the unchanged Primary convergence outcome.
- [ ] If needed, separately define the Optional non-overlap sensitivity outcome and label it supporting only.
- [ ] Freeze the mtDNA and nuclear OXPHOS gene lists.
- [ ] Freeze the exact sex/APOE comparison for the shared claim.
- [ ] Freeze the main cell context for each candidate.
- [ ] Freeze the expected direction for each system.
- [ ] Freeze each local module.
- [ ] Audit gene overlap between every local module and the shared endpoint.
- [ ] Freeze a non-circular candidate or upstream bridge measurement for each system.
- [ ] Mark a bridge `not_testable` if no scientifically meaningful nonoverlapping measurement remains.
- [ ] Freeze the q-value, CI, bootstrap, leave-one-donor-out, and donor-count rules.

### Round 1: donor-level evidence

- [ ] Build one RNA profile per donor and cell context.
- [ ] Test C1 directly; do not compare separate significance labels.
- [ ] Test C2 directly between cell types if using cell-type-specific language.
- [ ] Test C3 using the frozen mitonuclear endpoints.
- [ ] Test each candidate's named partner/readout and target-excluded local module.
- [ ] Build the frozen nonoverlapping bridge measurements without emptying the ATP-synthase program.
- [ ] Check that each local program and the residual endpoint show the same planned modifier comparison.
- [ ] Run the supporting donor-level bridge association.
- [ ] Run bootstrap, leave-one-donor-out, scoring, and quality sensitivities.
- [ ] Fill the evidence matrix without looking only at the figures.
- [ ] Decide how many candidates are authorized for Round 2.

### Round 2: network evidence

- [ ] Run corrected KDA only for authorized candidates.
- [ ] Run query-matched null comparisons.
- [ ] Run topology-matched null comparisons.
- [ ] Test stability after small network changes.
- [ ] Test an alternative donor-level network.
- [ ] Remove shared genes and test whether the remaining systems are distinct.
- [ ] Count how many candidates pass every required network rule.

### Round 3: independent RNA and protein support

- [ ] Test the frozen shared endpoint in independent RNA data.
- [ ] Test candidate links only where the required genes and groups are available.
- [ ] Test protein support where proteins were measured.
- [ ] Label a protein absent from the assay as `not_measured`; use `not_testable` when data exist but the planned comparison cannot be estimated.
- [ ] Rewrite the conclusion so it names exactly the number of supported systems.

---

## 14. The safest final wording at different evidence levels

If all three pass the stable Round 1 donor checks:

> The three candidate systems show donor-level expression patterns compatible with the same prespecified mitonuclear endpoint in their planned cell contexts.

If all three also pass Round 2:

> Three separately evaluated, network-nominated systems are associated with the same prespecified mitonuclear transcriptional endpoint through distinguishable cell-context-resolved expression programs.

If the endpoint is then independently replicated:

> The mitonuclear transcriptional endpoint was replicated in an independent cohort, while three network-nominated systems passed the planned donor and network checks for association with that endpoint.

Only add that an individual candidate was independently supported if that candidate's required external measurements actually passed.

Do **not** write the following without direct perturbation and functional experiments:

> The three systems cause the mitonuclear change or drive mitochondrial dysfunction in Alzheimer disease.

---

## 15. Final answer to the two original questions

### Question 1: How do we show that the three systems point to the same biological change?

Use two stages.

**Stage 1: test the core event once, without using any candidate.** The full C3 Gate 2 rule must pass, not just one residual result. C1 must also pass for the exact modifier wording, and C2 must pass only if we use “cell-type-specific.”

**Stage 2: test each candidate separately.** Each one must show:

1. the predicted local program in the correct cell context and frozen modifier comparison;
2. a stable, non-circular donor-level bridge using the Primary convergence outcome;
3. a network result that beats query-matched and topology-matched chance results;
4. support in an alternative network;
5. a distinguishable local program after shared genes are removed;
6. outside support when suitable independent RNA or protein data are available.

All three must pass separately for the same planned comparison and compatible endpoint direction before the sentence can say “three systems.”

### Question 2: Must one candidate system explain C1, C2, and C3?

No. C1–C3 test separate parts of the main event. The candidate systems are context-specific gene programs that may be associated with it. They cannot prove C1–C3, cannot rescue a failed core clause, and cannot be called causes without laboratory experiments.

---

## Related main plan

The complete workflow, input files, analysis models, output files, and gate rules are in:

[`mitochondrial_deep_dive_next_steps_plan.md`](./mitochondrial_deep_dive_next_steps_plan.md)
