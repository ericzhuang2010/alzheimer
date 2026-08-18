# Meeting Summary and Professor Action Items

## Meeting summary

You presented an updated analysis of **key driver analysis (KDA) genes**, incorporating feedback from earlier meetings. The presentation covered:

- How candidate genes were selected from the circular/network results using several filtering "gates."
- Evidence supporting the candidates across runs and networks.
- Comparison of mitochondrial and non-mitochondrial key drivers.
- Validation against public human-genetics resources.
- Detailed regulatory-network and STRING-DB protein-interaction analyses.

*Source: meeting transcript, lines 119-191.*

Your filtering produced **78 passing gene-run pairs, 47 gene-network pairs, and 25 unique candidate genes** for further analysis.

*Source: meeting transcript, lines 1341-1352.*

The results pointed toward mitochondrial respiration-related genes, including a strong MTCO2-related signal, and toward ribosomal genes among the non-mitochondrial candidates.

*Source: meeting transcript, lines 1356-1381.*

You then compared the candidates with public human-genetics evidence. Only a small subset had direct support in the database you used, including APOE in astrocytes.

*Source: meeting transcript, lines 1761-1776.*

Finally, you showed regulatory and protein-interaction networks for selected candidates, including upstream regulators and STRING-DB connections.

*Source: meeting transcript, lines 1921-1940.*

The professor's main reaction was that the work was promising - the professor explicitly said, "This is good" - but the presentation and validation strategy need to be made clearer and extended.

*Source: meeting transcript, lines 2775-2789.*

## What the professor wants you to do

### 1. Clearly define every filtering criterion

The professor did not immediately understand what you meant by a **"usable run."** You should state directly on the slide that a usable run must satisfy the relevant query-size or returned-gene requirement, rather than explaining it only after being asked.

*Source: meeting transcript, lines 297-337.*

You should also clearly separate:

- **Usable run**
- **Supporting run**
- The enrichment requirement
- The p-value threshold
- The final q-value threshold

The discussion indicates that a supporting run involved a p-value below 0.05 and enrichment greater than one, while the final filtering involved a q-value below 0.05.

*Source: meeting transcript, lines 368-385 and 447-468.*

**Concrete deliverable:** Add a small methods box or flowchart that defines all three gates and shows how the analysis goes from all run-gene pairs to 78 pairs, 47 gene-network pairs, and 25 genes.

### 2. Explain the plots so that a new audience can understand them

The professor repeatedly asked what the axes, symbols, lines, and ordering meant. In particular, the professor asked about:

- The meaning of "stability."
- The x-axis.
- The different symbols.
- Which studies or networks the symbols represented.
- The ordering of the many plotted lines.
- What retention values of zero and one meant.

*Source: meeting transcript, lines 799-905 and 968-1029.*

You eventually explained that retention of one means removing the fine cell type has essentially no effect, while an intermediate value indicates some impact. That explanation should be placed directly in the figure caption or legend.

*Source: meeting transcript, lines 1060-1072.*

**Concrete deliverable:** For every quantitative figure, add:

- A descriptive title stating the conclusion.
- Full x- and y-axis labels.
- A legend defining every symbol, color, and line.
- A sentence explaining how rows or lines are ordered.
- A caption defining what values such as retention = 0 and retention = 1 mean.
- Labels identifying the corresponding study, run, network, cell type, or APOE/sex group.

### 3. Make the figures readable and export them in publication-quality formats

The discussion about the detailed figure showed that the current embedded image was difficult to inspect. You offered a larger image, PDF, and SVG, and there was discussion of revising the code to export an editable vector-format figure.

*Source: meeting transcript, lines 1423-1508.*

**Concrete deliverable:** Regenerate the important figures as **SVG and high-resolution PDF**, with readable text at normal slide size. Avoid relying on screen zoom during the presentation.

### 4. Rewrite the human-genetics validation slide and explain the variant-to-gene mapping

The professor asked several times how genetic variants were converted or mapped to genes. The existing explanation - using public variant/gene labels and examining Alzheimer's-related variants - was not sufficiently precise.

*Source: meeting transcript, lines 1668-1749.*

You need to state:

- Which GWAS or genetics resource was used.
- Whether you started from variants, loci, or mapped genes.
- The exact variant-to-gene mapping rule.
- Whether the mapping was based on proximity, annotations, eQTL/sQTL evidence, published assignments, or another method.
- Whether mitochondrial variants were present in the source data.
- What counts as "support" for one of your KDA candidates.

**Concrete deliverable:** Add a reproducible methods paragraph and a schematic such as:

`GWAS/resource -> selected AD-associated variants -> variant-to-gene mapping method -> overlap with KDA gene-cell-type pairs`

### 5. Look specifically for mitochondrial genetic datasets

The professor pointed out that the lack of human-genetics support for mitochondrial genes may not be negative evidence. Many standard analyses may omit or inadequately analyze mitochondrial-genome variants. The professor suggested finding genetics resources that specifically include mitochondrial information.

*Source: meeting transcript, lines 1800-1817.*

You agreed that the current resource might not include mitochondrial data and that you could investigate the issue more deeply.

*Source: meeting transcript, lines 1822-1909.*

**Concrete deliverable:** Determine whether the current GWAS/genetics dataset contains mitochondrial variants. If not, identify a mitochondrial-genetics or mitochondrial-GWAS dataset relevant to Alzheimer's disease or the studied phenotype and repeat the candidate-overlap analysis.

### 6. Clarify how the regulatory neighborhoods are constructed

For the network figures, the professor wanted a precise definition of the "neighborhood":

- Is it one, two, or three network layers?
- Are the nodes upstream, downstream, or both?
- What rule determines which genes are included?
- Which edges come from your inferred network versus STRING-DB?
- What does each edge or edge color represent?

*Source: meeting transcript, lines 2158-2249.*

The later discussion also confirmed that you should explicitly say that your gene list was submitted to STRING-DB and that STRING-DB returned evidence-based connections among those proteins. The colors or edge types also need definitions.

*Source: meeting transcript, lines 2433-2483.*

**Concrete deliverable:** Add a network-methods legend defining:

`seed/key driver -> upstream/downstream radius -> node inclusion rule -> edge source -> edge/color meaning`

### 7. Try a three-step network visualization

The professor suggested showing a **three-step network**, at least as a visualization option. You explained that two levels may give better coverage and readability, but agreed that a third level could be included. The professor clarified that the suggestion was primarily for visualization.

*Source: meeting transcript, lines 2037-2097.*

**Concrete deliverable:** Generate both a two-step and three-step version for one or two representative candidates. Use the two-step figure in the main presentation if it is clearer, and place the three-step version in supplementary slides.

### 8. Check unresolved regulation in the RPL11 network

During the RPL11 discussion, a three-level downstream region or side cluster appeared to lack a clearly identified regulator. You said you would need to check whether anything regulates the genes in that part of the figure.

*Source: meeting transcript, lines 2531-2555.*

**Concrete deliverable:** Trace the upstream regulators of those nodes and determine whether the apparent disconnected or weakly connected region is biological, caused by the chosen network radius, or caused by missing edges.

### 9. Validate the human result in a mouse or other independent dataset

The professor suggested checking whether the mitochondrial pattern also appears in another dataset, particularly a mouse dataset. However, the professor cautioned that the mouse dataset may be smaller and have lower statistical power than the human dataset. Therefore, lack of statistical significance in mouse should not automatically be interpreted as disagreement.

*Source: meeting transcript, lines 2793-2837.*

The professor suggested examining whether the **direction or trend** is consistent with the human results and possibly using an approach that accounts for the difference in power.

*Source: meeting transcript, lines 2840-2867.*

This sounded like a useful but somewhat exploratory addition - the professor also said they were not yet certain whether it was necessary.

*Source: meeting transcript, lines 2864-2879.*

**Concrete deliverable:** In an independent mouse dataset, compare:

- Direction of effect.
- Rank or enrichment of the candidate genes.
- Cell-type consistency.
- Mitochondrial pathway-level enrichment.
- Confidence intervals or effect sizes, rather than significance alone.

Use this comparison to help narrow the candidate list.

### 10. Search for additional human or animal datasets

At the end of the meeting, you discussed further human or animal data associated with the original sex-by-APOE paper. The professor indicated that additional human data might exist and asked about applying the analysis to another dataset, since the current application had not used one.

*Source: meeting transcript, lines 2952-3000.*

**Concrete deliverable:** Revisit the original paper and its supplements/data-access statements, identify any additional human or animal datasets, and determine which can be used as an independent replication dataset.

## Recommended priority order

1. **Fix slide clarity:** definitions, axes, symbols, ordering, captions, and figure quality.
2. **Document the genetics methodology:** especially variant-to-gene mapping and the limitations of the current genetics resource.
3. **Investigate mitochondrial-specific genetics data.**
4. **Clarify and regenerate the network visualizations**, including the two- versus three-step comparison.
5. **Check the unresolved RPL11 regulatory region.**
6. **Evaluate an independent mouse or additional human dataset**, using effect direction and pathway-level trends when power is limited.

## Interpretation note

Because the transcript has no speaker labels and contains substantial automatic-transcription errors, the speaker roles were inferred from the question-and-answer flow. The items above are the requests most clearly supported by the conversation; the mouse comparison appears more optional than the presentation and genetics-method revisions.

## Source file

`meeting_recording_08182026_raw.txt`
