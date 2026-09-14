# Suggestions for Analyzing and Discussing Sex/APOE-Stratified Mitochondrial Key-Driver Results in Alzheimer's Disease

**The next step is to turn your 42 sets of results into a few biological questions—not to write 42 separate gene-list discussions.** I would organize the analysis around three questions:

1. **Which mitochondrial changes and candidate drivers are shared across categories?**
2. **Which appear to depend on cell type, sex, or APOE—and is that dependence supported statistically?**
3. **Which driver–mitochondrial-program relationships have enough evidence to justify focused biological interpretation and follow-up?**

Your results already contain promising leads, particularly the recurrent ribosomal genes and **SELENOM/SELENOW**. However, several distinctions in your slides are important for interpreting them correctly.

## 1. What your current results establish—and what they do not

Your actual workflow is more specific than “finding drivers of all DEGs.” The slides describe **AD-versus-NCI comparisons within fine cell types and sex–APOE groups, selection of mitochondrial DEGs as the KDA query, and aggregation of returned drivers into broad-cell categories**. Thus, the biological question is approximately:

> **Which network genes are associated with the mitochondrial transcriptional changes observed in particular cell-type, sex, and APOE contexts?**

That is a useful and focused research question. A candidate driver does not have to be differentially expressed or belong to your mitochondrial gene set. However, its identification is a **network prediction**, not direct evidence that experimentally changing that gene would alter the mitochondrial DEGs. [^slides-253-289]

The ROSMAP analysis reports **228 distinct non-MT genes, forming 381 gene-by-category combinations across 29 categories**, rather than observed drivers in all 42 possible categories. The slides also distinguish completed KDA calls with no significant returns from comparisons that could not be tested. Preserve that distinction throughout the analysis. [^slides-490-514] [^slides-350-408]

There is also an important connection to your proposal: the proposal’s primary questions concern **mitochondrial respiratory programs and mitochondrial–nuclear OXPHOS coordination**. KDA can help nominate genes associated with those changes, but it does not replace the program-level or coordination analyses. I would treat KDA as the explanatory and candidate-prioritization layer on top of those primary results. [^proposal-27-50]

**The strongest eventual story would therefore connect three levels:**

> **A mitochondrial program changes → that change differs across biological contexts → particular candidate drivers are linked to the affected program.**

The slides currently support identifying leads for that story, but they do not contain the complete driver tables, network neighborhoods, donor-level effects, or cross-cohort overlap results needed to finish it.

## 2. Similar studies worth using as models

These four papers are particularly relevant. The useful lesson is not merely which genes they found, but **how they moved from gene lists to biological arguments**.

| Study | What the researchers did | What to borrow for your project |
|---|---|---|
| **Guo et al., 2023, “Sex specific molecular networks and key drivers of Alzheimer’s disease,” Molecular Neurodegeneration** | Integrated MSBB and ROSMAP data, compared sex-specific networks, prioritized **LRP10**, and followed it with human RNA/protein measurements and sex/APOE-stratified mouse perturbation studies. | This is the closest conceptual match. Move from a broad driver landscape to a small number of candidates, inspect their neighborhoods, and evaluate context-specific evidence. You do not need to reproduce the experimental work to use the computational structure. ([link.springer.com](https://link.springer.com/article/10.1186/s13024-023-00624-5)) |
| **Yu et al., 2026, “Single-cell transcriptomic analysis reveals APOE genotype-dependent sex differences in Alzheimer’s disease,” Alzheimer’s & Dementia** | Compared AD-associated expression changes across six sex–APOE groups and 54 cell types, examined shared/divergent patterns, performed pathway analysis, and developed focused gene examples such as **CLU**. | Organize results around shared versus divergent biological programs, then use a few genes to explain those patterns. Because your proposal uses this study’s framework and ROSMAP resource, agreement with it is context—not independent validation. ([pmc.ncbi.nlm.nih.gov](https://pmc.ncbi.nlm.nih.gov/articles/PMC13158137/?utm_source=chatgpt.com)) [^proposal-119-124] |
| **Wu et al., 2025, “Single-cell landscape of sex-specific drivers of Alzheimer’s disease,” Alzheimer’s & Dementia** | Tested sex-dependent associations with amyloid, tau, cognition, and cognitive decline; used interaction models and sought replication in SEA-AD. | Consider relationships with disease severity and cognition, not only AD/NCI status. Borrow the distinction between sex-stratified associations and direct evidence that the associations differ by sex. ([pubmed.ncbi.nlm.nih.gov](https://pubmed.ncbi.nlm.nih.gov/41457042/?utm_source=chatgpt.com)) |
| **Beckmann et al., 2020, “Multiscale causal networks identify VGF as a key regulator of Alzheimer’s disease,” Nature Communications** | Combined RNA, protein, and network evidence; prioritized **VGF**; pursued independent replication, genetic support, and experimental testing. | Rank candidates using several different kinds of evidence rather than only their smallest KDA P value or recurrence count. ([pubmed.ncbi.nlm.nih.gov](https://pubmed.ncbi.nlm.nih.gov/32770063/?utm_source=chatgpt.com)) |

Taken together, these papers suggest a productive structure: **describe the overall pattern, identify coherent biological programs, select representative drivers, and strengthen the interpretation using evidence not already built into the discovery procedure.**

## 3. The analyses I would prioritize

### A. Identify the mitochondrial programs associated with each category

Before discussing why a driver might matter, determine **what mitochondrial process is changing in that category**.

For your primary analysis, retain the four programs specified in the proposal: mitochondrial-DNA-encoded OXPHOS, nuclear-encoded OXPHOS structural genes, mitochondrial translation, and inner-membrane/MICOS-related programs. Additional mitochondrial pathways can be explored afterward, clearly labeled exploratory. MitoCarta3.0 provides a curated mitochondrial inventory and pathway annotations suitable for this purpose. [^proposal-164-195] ([broadinstitute.org](https://www.broadinstitute.org/mitocarta/mitocarta30-inventory-mammalian-mitochondrial-proteins-and-pathways?utm_source=chatgpt.com))

I would analyze three different gene sets separately:

| Gene set | Question it answers | Important interpretation issue |
|---|---|---|
| **All genes tested in differential expression**, using signed results | Which biological programs show coordinated AD-associated expression changes? | A ranked analysis can use information beyond the arbitrary significant-DEG cutoff. |
| **Mitochondrial DEGs** | Which mitochondrial processes account for the category’s mitochondrial signature? | The background should reflect mitochondrial genes that were actually eligible to be detected and tested. |
| **Candidate drivers and their network neighborhoods** | What kinds of genes are associated with those mitochondrial changes, and which parts of the mitochondrial signature do they connect to? | Driver functions and target functions are different questions; do not merge them into one enrichment analysis. |

A ranked gene-set approach such as GSEA is useful for the first question because it evaluates coordinated changes across a gene set rather than requiring every member to pass a DEG threshold. Use an appropriate signed differential-expression statistic, not the unsigned KDA ranking score. ([pmc.ncbi.nlm.nih.gov](https://pmc.ncbi.nlm.nih.gov/articles/PMC1239896/?utm_source=chatgpt.com))

**The main figure should be a pathway-by-category heatmap**, ideally showing direction and effect size, with statistical support indicated separately. A heatmap containing only enrichment P values cannot show whether a program increases or decreases.

Also avoid a circular conclusion: because mitochondrial genes were deliberately selected as KDA inputs, “the results involve mitochondria” is not a new finding. The informative result is **which mitochondrial program, in which context, and with which candidate network relationships**.

### B. Separate shared drivers from context-associated drivers

Your recurrence results are a natural starting point. The slides report **RPS15 in 11 categories, RPL11 in 10, RPLP1 in eight, RPL15 and SELENOM in seven each, and SELENOW in six**. Those are descriptive patterns worth investigating. [^slides-517-536]

Construct a complete **gene × 42-category matrix**, using all returned drivers rather than only the top five. For every gene–category pair, preserve whether the gene was returned, was evaluated but not returned, or could not be evaluated. Where available, add the number of contributing fine-cell contrasts and the number in which the gene was actually eligible for testing.

Then ask whether recurrence is organized primarily by **cell type, APOE, sex, or a combination**. For example, does a candidate recur across all six sex–APOE groups but mainly in neurons? That suggests a different story from a candidate occurring across several cell types only in female ε4 carriers.

For fine-cell support, a useful descriptive quantity is:

$$
\text{support fraction}
=
\frac{\text{eligible fine-cell calls returning the driver}}
{\text{fine-cell calls in which that driver was actually evaluated}}.
$$

This is more informative than a numerator alone, although it is still not a formal test of biological specificity.

You can also compare category pairs using driver overlap and, more importantly, **overlap of the mitochondrial programs or target genes associated with their drivers**. Two categories might have different top genes but converge on the same respiratory program. Conversely, the same driver might connect to different mitochondrial signatures in different categories.

**Do not equate “returned only in females” with “female-specific.”** Your proposal correctly calls for direct modifier contrasts rather than inferring a difference because one group is significant and another is not. Until those tests are done, use wording such as “prioritized in the female ε4 category” or “detected only in this category under the current analysis.” [^proposal-173-179]

### C. Examine the actual mitochondrial neighborhoods of the strongest drivers

This is probably the most important missing step between your current slides and a strong Discussion.

For a candidate such as **RPS15, RPL11, SELENOW, or SELENOM**, extract the neighborhood used by the KDA method and identify exactly which mitochondrial query genes occur within it. KDA methods prioritize nodes partly through enrichment of a signature in their network neighborhoods; examining that neighborhood reveals what produced the nomination. ([nature.com](https://www.nature.com/articles/s41467-020-17405-z))

For each shortlisted driver, assemble a small evidence record containing:

- The relevant category and supporting fine cell types.
- The mitochondrial query genes in its neighborhood, their AD/NCI expression changes, and their pathway assignments.
- Neighborhood size, query coverage, enrichment, and stability under sensitivity analyses.

Here, query coverage can be defined as:

$$
\text{coverage}
=
\frac{\text{mitochondrial query genes in the driver’s neighborhood}}
{\text{mitochondrial genes in that query}}.
$$

Call these **network-associated genes** or **predicted downstream genes**, depending on what the actual network model supports—not experimentally established targets.

The key biological questions are then concrete. Does SELENOW connect primarily to respiratory-chain genes, mitochondrial translation genes, or a mixed signature? Does RPS15 connect to the same program in different categories? Are RPS15 and RPL11 essentially two representatives of one overlapping subnetwork?

If several candidates have nearly identical neighborhoods, discuss them as a **candidate module**, rather than presenting each as an independent mechanism.

I would also check whether a candidate’s apparent importance exceeds what would be expected for other genes with similarly large neighborhoods and similar expression levels. This helps distinguish a mitochondrial-signature-associated candidate from a generally well-connected gene.

### D. Directly test the sex/APOE differences that you intend to discuss

Choose a limited set of program-level and candidate-associated hypotheses, following your prespecified priorities.

For example:

> Does the AD-associated change in a respiratory-program score differ between females and males among ε4 carriers?

The relevant contrast is:

$$
(\mathrm{AD}-\mathrm{NCI})_{\mathrm{female},\,\varepsilon4}
-
(\mathrm{AD}-\mathrm{NCI})_{\mathrm{male},\,\varepsilon4}.
$$

An analogous contrast compares the AD effect in ε4 carriers against ε3/ε3 donors within a sex. Your proposal already specifies this difference-in-differences logic. [^proposal-133-146]

The outcome could be a prespecified mitochondrial-program score or, exploratorily, a score based on a frozen driver-associated mitochondrial gene set. A driver’s own expression can also be tested, but **a driver need not be a DEG**, so expression change should not become an absolute requirement for retaining it. [^slides-285-289]

Report estimated differences and confidence intervals, not only significance labels. Sparse groups may support only uncertain or nonestimable comparisons.

One additional methodological check matters: **is the same broad-cell network used for all six sex–APOE strata?** If so, differences in returned drivers arise from applying different DEG queries to that network. They do not, by themselves, demonstrate that network connections have changed between sexes or genotypes.

### E. Prioritize a few candidates using multiple evidence types

I would not select every category’s top-ranked gene for detailed discussion. Instead, choose approximately **three to five representatives** that collectively explain your strongest patterns.

My provisional shortlist for investigation—not a final biological ranking—would include a recurrent ribosomal representative such as **RPS15 or RPL11**, **SELENOW**, **SELENOM**, and a more cell-context-focused candidate such as **PGK1**, which appears in several astrocyte rows in the top-five figure. [^slides-453-461] [^slides-517-536]

For each candidate, weigh **network support, fine-cell consistency, mitochondrial-program coherence, donor-level evidence, robustness, independent-cohort support, and relevant experimental literature**.

This should be an evidence table rather than an opaque score with arbitrary weights. Keep “previously implicated in AD” separate from “supported by our analysis.” A familiar gene is not automatically the strongest result, and an unfamiliar gene is not automatically unimportant.

### F. Make SEA-AD validation specific about what was actually tested

The SEA-AD summary currently shows **22 KDA calls and 44 gene-by-category combinations**, representing 43 genes in five categories; **20 of the 22 calls are M_e33**. This is a limited and uneven validation opportunity, not a test of all 42 discovery categories. [^slides-199-222]

Also, **44 SEA-AD results do not mean 44 ROSMAP findings replicated**. The slides do not show the matched discovery–validation overlap.

I would assess three levels separately:

**Gene–category replication:** Does the same driver receive support in the same broad cell type and sex–APOE group, among genes and categories that were evaluable in both cohorts?

**Program replication:** Does the same mitochondrial program show a compatible AD-associated effect? This remains informative when individual driver rankings differ.

**Driver-associated gene-set replication:** Does a mitochondrial gene set defined from a ROSMAP driver neighborhood show a coherent, compatible pattern in SEA-AD? Freeze the gene set before testing SEA-AD.

Because SEA-AD uses cohort-specific networks, differences can reflect both expression differences and differences in network construction. Keep **expression-program replication** separate from **re-identification by an independently constructed network**.

Where a comparison was not possible, report “not evaluable,” not “failed replication.” The Wu study is a useful example of explicitly considering phenotype harmonization, cohort differences, and limited replication power. ([alz-journals.onlinelibrary.wiley.com](https://alz-journals.onlinelibrary.wiley.com/doi/pdfdirect/10.1002/alz.71041))

## 4. Biological discussion themes already suggested by your results

These are **hypotheses to investigate**, not conclusions established by the current slides.

### Theme 1: Cytosolic translation may be associated with mitochondrial transcriptional remodeling

The recurrence of RPS15, RPL11, RPLP1, and RPL15 makes translation-related biology a reasonable starting point. An essential distinction is that **RPS15 and RPL11 are cytosolic ribosomal proteins**, not mitochondrial ribosomal proteins. Their identification therefore does not directly demonstrate altered mitochondrial translation. [^slides-517-536] ([ncbi.nlm.nih.gov](https://www.ncbi.nlm.nih.gov/gene/6209?utm_source=chatgpt.com))

There is relevant experimental precedent: Ding and colleagues reported impaired ribosome function and protein synthesis in cortical tissue from individuals with MCI and AD. That provides biological context, but it does not establish the role of your particular drivers or their sex/APOE dependence. ([pubmed.ncbi.nlm.nih.gov](https://pubmed.ncbi.nlm.nih.gov/16207876/?utm_source=chatgpt.com))

The most useful next question is:

> Are these cytosolic ribosomal candidates associated with a coherent mitochondrial program, or are they recurring because they represent a broad expression/network feature?

Compare their target overlap, mitochondrial-program associations, and sensitivity to expression level, network connectivity, and donor quality.

A defensible discussion sentence would be:

> “The recurrent prioritization of cytosolic ribosomal genes raises the possibility that translation-related networks are associated with mitochondrial transcriptional remodeling in AD. Whether this represents a specific biological relationship rather than a general network or expression property requires further testing.”

### Theme 2: SELENOW and SELENOM provide biologically interesting, but distinct, follow-up hypotheses

Your recurrence summary identifies both genes, making them worth examining beyond their rank. [^slides-529-536]

**SELENOW has especially relevant experimental literature.** Ren et al., in *Communications Biology* in 2024, investigated SELENOW in cell and mouse models, reporting effects on tau homeostasis and evidence involving the ubiquitin–proteasome system. This makes SELENOW more than a gene with a generic antioxidant annotation. However, that study does not establish that SELENOW controls your mitochondrial DEG signatures or explains your sex/APOE patterns. ([nature.com](https://www.nature.com/articles/s42003-024-06572-0?utm_source=chatgpt.com))

For **SELENOM**, experimental work in neuronal and cortical cultures links its manipulation to oxidative-stress responses, cell viability, and cytosolic calcium regulation. Again, this is supporting biological context rather than validation of your inferred network relationships. ([ncbi.nlm.nih.gov](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2864655/?utm_source=chatgpt.com))

I would investigate whether the two genes connect to the same mitochondrial programs or to different ones. Do not merge them into a single “selenoprotein mechanism” merely because both are selenoproteins.

An appropriate framing is:

> “The recurrence of SELENOW and SELENOM nominates candidate connections between mitochondrial expression signatures and previously studied tau/protein-homeostasis, oxidative-stress, or calcium-related processes. The relevant connections in our data remain to be defined through their associated mitochondrial genes.”

### Theme 3: Astrocyte-associated candidates may connect mitochondrial changes with other metabolic programs

The top-five figure includes **PGK1** in several astrocyte categories. PGK1 is a glycolytic enzyme, so one focused follow-up is to compare glycolysis-related expression with the prespecified respiratory-program scores in those categories. [^slides-453-461] ([ncbi.nlm.nih.gov](https://www.ncbi.nlm.nih.gov/gene/?term=ENSG00000102144&utm_source=chatgpt.com))

This could support a discussion of coordinated or opposing **transcriptional** metabolic programs. It would not establish a metabolic switch, increased glycolytic flux, or compensation for impaired respiration.

Similarly, the larger number of returned driver-category units in excitatory and inhibitory neurons makes neuronal patterns worth investigating, but does not show that neurons are necessarily more affected: those counts are conditioned on unequal opportunities to run KDA and obtain returns. [^slides-508-543]

### Where the novelty could lie

Yu et al. already discussed translation-related, mitochondrial, and heat-shock-related patterns in the sex/APOE-stratified AD setting. Therefore, “translation and mitochondria are implicated” would not be the strongest novelty claim. ([alz-journals.onlinelibrary.wiley.com](https://alz-journals.onlinelibrary.wiley.com/doi/pdfdirect/10.1002/alz.71463))

Your potential contribution is more specific:

> **Identifying which candidate network genes connect to particular mitochondrial programs, determining the biological contexts in which those relationships appear, and establishing how robustly they reproduce.**

## 5. Two checkpoints before making strong claims

### The current ACAT results are exploratory rankings

Your slides explicitly state that the category scores combine **returned within-call BH-adjusted P values**, omit contrasts where a gene was not returned, and lack final across-gene FDR control. They appropriately describe those scores as exploratory. [^slides-153-174] [^slides-453-461]

ACAT is a P-value combination method; it does not automatically correct for selecting only significant inputs before combination. Consequently, I would use the current score for prioritization, not label it a final category-level FDR or proof of repeated independent support. ([asc.ohio-state.edu](https://www.asc.ohio-state.edu/statistics/statgen//joul_spr2020/ACAT.pdf?utm_source=chatgpt.com))

Before confirmatory claims, consider a prespecified aggregation using the full set of eligible tests and preferably their raw P values, or a suitably designed null analysis that reproduces the selection and aggregation procedure. Do not invent P values for unavailable tests. Recurrence across fine cell types also does not create independent donor replication when the same donors contribute to those cell types.

### Verify donor-level replication in the DEG analysis

The proposal specifies the **donor as the independent biological sample**, whereas the slides describe an upstream MAST comparison and a minimum-cell execution rule without documenting the full donor model. This does not prove a problem, but it needs verification. [^proposal-125-127] [^slides-367-408]

Confirm that the DEG analysis accounts for donor-to-donor variation, through an appropriate mixed model or donor-level pseudobulk analysis. A minimum number of cells is not a substitute for adequate independent donors. This matters because the mitochondrial queries—and therefore the KDA results—depend on the upstream DEG analysis. Benchmarking by Squair et al. demonstrates the importance of accounting for biological-replicate variation in single-cell differential expression. ([nature.com](https://www.nature.com/articles/s41467-021-25960-2?utm_source=chatgpt.com))

For shortlisted findings, prioritize donor resampling, leave-one-donor-out checks, reasonable DEG-threshold sensitivity, and inspection of dependence on a single fine cell type. Your proposal already includes several of these checks. [^proposal-201-208]

## 6. How I would organize the final Discussion and figures

I would write the Discussion as a connected argument with five parts.

**First, state the main supported pattern.** Describe the mitochondrial programs and candidate-driver patterns that survived your checks. Separate observed results from hypotheses; do not begin with an inventory of 228 genes.

**Second, discuss shared biology.** Explain whether recurrent candidates represent overlapping translation-related, stress-related, or other modules. Relate them to prior studies and explain what your network analysis adds.

**Third, discuss context dependence.** Focus on the strongest cell-type, sex, and APOE contrasts, distinguishing directly tested differences from descriptive category-restricted returns.

**Fourth, develop two or three candidate examples.** For each example, move through the same sequence: your observation → associated mitochondrial genes/program → relevant literature → alternative explanation → testable follow-up.

**Finally, evaluate validation and limitations.** Explain which findings reproduced, which were not evaluable, and which remained unstable. Preserve the proposal’s boundary: RNA abundance and inferred networks do not establish respiration, ATP production, causal regulation, or therapeutic benefit. [^proposal-237-242]

For figures, I would prioritize a **mitochondrial-program effect heatmap**, a **full driver-support matrix**, **two or three readable driver-neighborhood diagrams**, a **forest plot of direct sex/APOE contrasts**, and a **replication/robustness summary**. Keep the complete gene lists and detailed category tables in supplementary material.

**My practical recommendation is to start with the pathway heatmap and the mitochondrial neighborhoods of RPS15/RPL11, SELENOW, and SELENOM.** Those analyses will tell you whether the recurring names form a coherent biological story. Then use direct contrasts and SEA-AD to determine which parts of that story can be stated as supported findings, which remain plausible hypotheses, and which should be dropped.

---

## References to uploaded materials

The footnotes below preserve the uploaded-source references from the original response. Line ranges refer to the extracted text used in the conversation, not line numbering within Word or PowerPoint. External research references are linked inline above.

[^slides-253-289]: Uploaded slides: `09162026_sex_apoe_kda_fine_broad copy.pptx`, extracted-text lines 253–289.

[^slides-490-514]: Uploaded slides: `09162026_sex_apoe_kda_fine_broad copy.pptx`, extracted-text lines 490–514.

[^slides-350-408]: Uploaded slides: `09162026_sex_apoe_kda_fine_broad copy.pptx`, extracted-text lines 350–408.

[^proposal-27-50]: Uploaded proposal: `HSR_2026_27_mitochondria_sex_APOE_AD_proposal_draft.docx`, extracted-text lines 27–50.

[^proposal-119-124]: Uploaded proposal: `HSR_2026_27_mitochondria_sex_APOE_AD_proposal_draft.docx`, extracted-text lines 119–124.

[^proposal-164-195]: Uploaded proposal: `HSR_2026_27_mitochondria_sex_APOE_AD_proposal_draft.docx`, extracted-text lines 164–195.

[^slides-517-536]: Uploaded slides: `09162026_sex_apoe_kda_fine_broad copy.pptx`, extracted-text lines 517–536.

[^proposal-173-179]: Uploaded proposal: `HSR_2026_27_mitochondria_sex_APOE_AD_proposal_draft.docx`, extracted-text lines 173–179.

[^proposal-133-146]: Uploaded proposal: `HSR_2026_27_mitochondria_sex_APOE_AD_proposal_draft.docx`, extracted-text lines 133–146.

[^slides-285-289]: Uploaded slides: `09162026_sex_apoe_kda_fine_broad copy.pptx`, extracted-text lines 285–289.

[^slides-453-461]: Uploaded slides: `09162026_sex_apoe_kda_fine_broad copy.pptx`, extracted-text lines 453–461.

[^slides-199-222]: Uploaded slides: `09162026_sex_apoe_kda_fine_broad copy.pptx`, extracted-text lines 199–222.

[^slides-529-536]: Uploaded slides: `09162026_sex_apoe_kda_fine_broad copy.pptx`, extracted-text lines 529–536.

[^slides-508-543]: Uploaded slides: `09162026_sex_apoe_kda_fine_broad copy.pptx`, extracted-text lines 508–543.

[^slides-153-174]: Uploaded slides: `09162026_sex_apoe_kda_fine_broad copy.pptx`, extracted-text lines 153–174.

[^proposal-125-127]: Uploaded proposal: `HSR_2026_27_mitochondria_sex_APOE_AD_proposal_draft.docx`, extracted-text lines 125–127.

[^slides-367-408]: Uploaded slides: `09162026_sex_apoe_kda_fine_broad copy.pptx`, extracted-text lines 367–408.

[^proposal-201-208]: Uploaded proposal: `HSR_2026_27_mitochondria_sex_APOE_AD_proposal_draft.docx`, extracted-text lines 201–208.

[^proposal-237-242]: Uploaded proposal: `HSR_2026_27_mitochondria_sex_APOE_AD_proposal_draft.docx`, extracted-text lines 237–242.
