# Tutorial: understanding Section 22, “Astrocytic RPL13 appears in the circular overview but requires annotation correction”

**Source section:** [Joint Phase 11–12 synthesis](phase11_phase12_joint_mitochondrial_discussion.md)  
**Audience:** readers who want to distinguish an annotation artifact from a potentially valid network hypothesis  
**Purpose:** explain, sentence by sentence, why most displayed `RPL13` recurrence is not currently interpretable and why one corrected analysis could still retain `RPL13` as a candidate

The principal supporting files are the [circular-figure data](../../results/figures/analysis/phase12_kda/circular_figure/phase12_kda_circular_plotted_data.tsv), the [Phase 12 result rows](../../results/minerva_production/12_kda/kda_results.tsv), the [tested-gene annotation table](../../results/minerva_production/03_annotations/tested_gene_universe.tsv), and the [alias map](../../results/minerva_production/03_annotations/gene_alias_mapping.tsv).

## 1. The central idea

`RPL13` and `MRPL13` are two different genes. `RPL13` encodes a component of
the cytoplasmic 60S ribosomal subunit, whereas `MRPL13` encodes a component of
the mitochondrial 39S ribosomal subunit. The pipeline preserved the measured
feature as `RPL13` but classified it as a canonical mitochondrial gene after
matching the symbol to an `MRPL13` synonym. That cross-gene match allowed
`RPL13` to enter mitochondrial differential-expression signatures.

Phase 12 then tested whether directed network neighborhoods were enriched for
those signatures. In 17 of the 21 astrocytic result rows shown by the circular
overview, the `RPL13` candidate was also one of the query genes counted inside
its own neighborhood. Most of the apparent recurrence is therefore vulnerable
to candidate-self enrichment created by the annotation problem.

One primary directional result is different. In female-ε4 `Ast DPP10`
AD-down, `RPL13` is not a query member, yet its neighborhood contains four
other mitochondrial query genes and remains significant. That row preserves
a provisional hypothesis—cytoplasmic `RPL13` may sit upstream of an
astrocytic mitochondrial response—but it does not validate that hypothesis.
The annotation must be corrected and the analysis rerun before the candidate
is prioritized.

## 2. Vocabulary

| Term | Meaning in Section 22 |
|---|---|
| **`RPL13`** | The measured gene, with Ensembl ID `ENSG00000167526` and NCBI Gene ID 6137; it encodes a cytoplasmic 60S ribosomal protein. |
| **`MRPL13`** | A distinct gene, with Ensembl ID `ENSG00000172172` and NCBI Gene ID 28998; it encodes a mitochondrial 39S ribosomal protein. |
| **Official or canonical symbol** | The current approved short name used to identify a gene. An alias must not override the stable identity of a different official gene. |
| **Synonym or alias** | An alternative historical name. Alias matching is useful, but it can misassign a feature when an alias is also another gene's current official symbol. |
| **Stable gene identifier** | An identifier such as Ensembl, NCBI Gene, or HGNC ID that distinguishes genes even when symbols or aliases are confusing. |
| **MitoCarta** | A curated inventory of human mitochondrial proteins. It includes many nuclear-encoded genes, so a valid member does not need an `MT-*` symbol. |
| **Mitochondrial query or signature** | The direction-specific set of significant mitochondrial genes whose concentration in a network neighborhood is tested by KDA. |
| **KDA candidate** | A network gene whose directed neighborhood is tested for enrichment. The candidate does not itself need to be mitochondrial. |
| **Candidate-self overlap** | A result in which the candidate is also a query member and contributes to the overlap count used by the enrichment test. |
| **Primary analysis** | A run for one prespecified sex/APOE group, such as female ε4. |
| **Secondary analysis** | A pooled run that reuses primary source groups, such as a female-only or ε4-only pool. It is not an independent cohort. |
| **Directional signature** | An `AD_up_mito` or `AD_down_mito` query containing genes with one AD-minus-NCI direction. |
| **Derived union** | An `AD_both_mito` query formed from the directional signatures for the same source contrast or pool. It is a second analysis of reused inputs, not a new biological confirmation. |
| **Global key driver** | A significant driver not placed within two downstream layers of another significant driver in the same run. “Global” does not mean universal across the study. |
| **Matched null** | A comparison that asks whether a result is stronger than expected for genes with similar expression, network degree, or biological class. |

## 3. How to read the title and evidence label

| Phrase | Precise meaning |
|---|---|
| **Astrocytic** | The displayed rows use the broad Astrocytes network and signatures from three fine astrocyte types: `Ast CHI3L1`, `Ast DPP10`, and `Ast GRM3`. |
| **RPL13 appears** | The descriptive figure selects the top five drivers per broad network. Appearance is a ranking outcome, not validation. |
| **Circular overview** | The figure summarizes recurrence, primary/secondary composition, fine-cell coverage, global-call share, and the most extreme per-row statistics. It does not perform a new meta-analysis. |
| **Requires annotation correction** | The `RPL13` feature was assigned mitochondrial status through `MRPL13`; the signatures and all dependent KDA summaries must be rebuilt after separating the genes. |
| **Annotation-constrained** | Interpretation is limited by a known upstream identity problem. More discussion of the existing P values cannot repair that input. |
| **Low-confidence network hypothesis** | One self-independent row is potentially informative, but it comes from one directional context in one reused broad network and lacks experimental validation. |

The phrase “non-mtDNA candidate” does not by itself imply an error. Most
mitochondrial proteins are encoded in the nucleus. The error is the conflict
between the stable identity of measured `RPL13` and the MitoCarta identity of
`MRPL13`, not the absence of an `MT-*` prefix.

## 4. Discovery paragraph, sentence by sentence

> **“`RPL13` is the one displayed non-mtDNA candidate that did not already
> have a dedicated discussion in this document.”**

The circular overview shows the five highest-ranked candidates within each
result-producing broad network. Other displayed candidates had already been
interpreted in earlier sections of the joint synthesis. This sentence explains
why Section 22 was added: it closes an editorial gap in candidate coverage.
It does **not** claim that `RPL13` is the only nuclear-encoded candidate or the
only non-`MT-*` label in the figure.

> **“It is the fifth-ranked astrocyte sector in the circular overview and
> recurs across three fine astrocyte types.”**

Within each broad network, the plotting script first orders candidates by the
number of significant calls, then uses minimum adjusted P value, maximum fold
enrichment, and gene name as tie-breakers. `RPL13` has 21 significant
Astrocytes-network rows and therefore occupies selection rank five. Those rows
come from `Ast CHI3L1`, `Ast DPP10`, and `Ast GRM3` signatures.

“Three fine astrocyte types” describes coverage, not three independent
networks. All three fine types query the same fixed broad Astrocytes network.
Likewise, the 21 rows are not 21 donor cohorts: primary union rows reuse
directional inputs, and secondary rows pool primary groups.

> **“Most of that recurrence, however, is entangled with a likely cross-gene
> synonym-mapping error between `RPL13` and `MRPL13`.”**

The tested-gene table records the measured feature and its GENCODE-resolved
identity as `RPL13`/`ENSG00000167526`. The same row records the MitoCarta
symbol as `MRPL13` and the match type as `unique_synonym`. The alias table
contains this path:

```text
measured feature RPL13
        ↓ stable GENCODE identity
RPL13 / ENSG00000167526
        ↓ synonym lookup used for MitoCarta matching
MRPL13 / mitochondrial-ribosome membership
        ↓ inherited classification
RPL13 labeled as a core mitochondrial protein
        ↓
RPL13 admitted to Phase 12 mitochondrial queries
```

“Unique” means the alias table returned one MitoCarta target. It does not mean
the biological identity was correct. Here, the alias is also the official
symbol of a different measured gene, so stable identifiers should take
precedence.

## 5. Conclusion paragraph, sentence by sentence

> **“The displayed recurrence should not currently be interpreted as evidence
> that RPL13 is a mitochondrial structural gene or a validated mitochondrial
> key driver.”**

This sentence rejects two distinct overstatements.

First, the result does not turn cytoplasmic RPL13 into mitochondrial MRPL13.
The proteins belong to different ribosomes and are encoded by different
genes. Second, a significant KDA row is a network-enrichment result, not a
perturbation experiment. Even a correctly annotated, self-independent row
would nominate `RPL13` as a candidate rather than validate it as a causal
driver.

The safe interpretation is narrower: the current figure contains an
`RPL13`-labeled network pattern whose majority depends on a questionable
mitochondrial-query assignment.

> **“Seventeen of its 21 plotted calls contain `RPL13` itself in the effective
> mitochondrial query.”**

The `overlap_items` field supplies the direct audit. In 17 rows, `RPL13`
appears among the query genes captured by its own selected network
neighborhood. Candidate-self membership raises the overlap count by one. That
can matter greatly when both the query and neighborhood are small.

This does not prove that every one of the 17 rows would become nonsignificant
after correction. It means their present P values, selected layers, fold
enrichments, and within-run multiple-testing results cannot be treated as
clean evidence. A post hoc subtraction is insufficient because removing a
query gene changes the signature size, overlap count, potentially the best
layer, and the Benjamini–Hochberg comparison among candidates.

> **“Of the four primary directional calls, only the female-ε4 `Ast DPP10`
> AD-down result is candidate-self-independent.”**

The four primary directional rows are:

| Fine type and group | Direction | RPL13 in overlap? | Overlap/query | Fold enrichment | Adjusted P |
|---|---|---:|---:|---:|---:|
| `Ast CHI3L1`, female ε2 | AD-up | Yes | 2/6 | 128.57 | 0.01268 |
| `Ast DPP10`, female ε4 | AD-down | **No** | 4/25 | 40.66 | 2.51×10^-4 |
| `Ast GRM3`, female ε2 | AD-up | Yes | 6/59 | 19.72 | 5.63×10^-5 |
| `Ast GRM3`, male ε2 | AD-down | Yes | 7/94 | 14.24 | 2.95×10^-5 |

The three self-containing rows cannot separate genuine mitochondrial
neighborhood concentration from the advantage created by counting the
candidate itself. The `Ast DPP10` row can, because its four overlap genes are
other genes.

> **“That one result supports a low-confidence astrocytic network hypothesis
> that can survive correction in principle, but the Phase 09 annotation and
> affected Phase 12 runs should be repaired and rerun before prioritizing
> RPL13 experimentally.”**

“Can survive correction in principle” means the `Ast DPP10` directional query
does not contain `RPL13`, so separating `RPL13` from `MRPL13` does not directly
remove one of that row's four overlaps. The candidate can still be tested as a
non-mitochondrial network gene.

The confidence remains low because this is one primary directional context,
the broad Astrocytes network is fixed rather than independently inferred for
`Ast DPP10`, the result is observational, and ribosomal genes may be favored by
expression level, network connectivity, or general stress biology. A clean
rerun is the minimum gate before committing biological samples or perturbation
experiments.

## 6. Data-driven evidence, sentence by sentence

> **“The circular overview reports 21 astrocyte calls across three fine cell
> types: eight primary, 13 secondary, and 19 global.”**

Each “call” is one significant `RPL13` row in one KDA run. The counts break
down as follows:

| Summary feature | Count | What it does—and does not—show |
|---|---:|---|
| Significant calls | 21 | Descriptive recurrence across run definitions, not 21 independent replications |
| Fine cell types | 3 | Coverage of `Ast CHI3L1`, `Ast DPP10`, and `Ast GRM3` signatures in one broad network |
| Primary calls | 8 | Four directional rows plus four reused `AD_both_mito` union rows |
| Secondary calls | 13 | Pooled analyses built from primary source groups |
| Global calls | 19 | RPL13 was an upstream representative among significant drivers in 19 individual runs |

The “global” flag is a within-run topology reduction. It does not mean RPL13
is important in every astrocyte type, group, network, or AD dataset. The two
non-global rows are the female-ε2 `Ast GRM3` directional and union results;
they remain significant rows but sit downstream of another significant driver
under the configured reduction rule.

The plotted-data row also shows 97 eligible Astrocytes-network runs, so the
displayed recurrence fraction is `21/97 = 0.2165`. This denominator is more
informative than reading 21 as a universal rate.

> **“Its minimum adjusted P is 9.76×10^-6 and its maximum fold enrichment is
> 128.57.”**

These are extrema selected from different rows, not one combined statistic.
The minimum adjusted P comes from the self-independent secondary `Ast DPP10`
female-pool AD-down row. The maximum fold enrichment comes from the
self-containing primary `Ast CHI3L1` female-ε2 AD-up row.

The adjusted P values are corrected across candidate drivers **within each
run**. The minimum across 21 rows is not a Phase 12-wide adjusted P value. The
fold enrichment is a concentration ratio for query genes inside a network
neighborhood; 128.57 is not an RNA expression fold change.

> **“The four primary directional contexts are female-ε2 `Ast CHI3L1` AD-up,
> female-ε4 `Ast DPP10` AD-down, female-ε2 `Ast GRM3` AD-up, and male-ε2
> `Ast GRM3` AD-down.”**

These are the four cleanest context labels for interpreting direction. Each
starts from one fine cell type, one sex/APOE group, and one AD-minus-NCI
direction. Their signs are mixed: two AD-up and two AD-down. KDA itself does
not infer whether RPL13 activates or represses the neighborhood, so the mixed
query directions must not be turned into a single RPL13 effect direction.

> **“Their four `AD_both_mito` rows reuse those directional inputs and are
> summaries, not four extra confirmations.”**

For each source contrast, `AD_both_mito` is the union of the AD-up and AD-down
mitochondrial genes. It can reveal enrichment for mitochondrial dysregulation
regardless of sign, but it uses the same donors, differential-expression
analysis, and broad network. Thus, the eight primary calls represent four
directional biological contexts analyzed in two query forms, not eight
independent discoveries.

> **“Exact-overlap reconstruction shows candidate-self overlap in 17 of the
> 21 plotted calls.”**

The result table records every captured query gene in `overlap_items`.
Counting rows in which that field contains `RPL13` gives:

| Result class | Self-containing | Self-independent | Total |
|---|---:|---:|---:|
| Primary directional | 3 | 1 | 4 |
| Primary `AD_both_mito` union | 3 | 1 | 4 |
| Secondary pooled | 11 | 2 | 13 |
| **Total** | **17** | **4** | **21** |

All four self-independent rows come from `Ast DPP10`: the female-ε4 primary
directional row and its union, plus the female-pool secondary directional row
and its union. Because the union and pooled rows reuse source information,
they do not create four independent validations of one mechanism.

> **“Three of the four primary directional calls are among those
> self-containing results.”**

This sentence identifies the central evidentiary problem. Primary directional
rows are normally the most interpretable tier because they preserve one
prespecified sex/APOE context and one expression direction. Here, three of
those four rows are precisely the rows most directly affected by the alias
collision.

> **“The candidate-self-independent female-ε4 `Ast DPP10` AD-down call uses a
> layer-3 RPL13 neighborhood of 24 genes and covers four of 25 query genes:
> `COX4I1`, `SLC25A3`, `ATP5F1B`, and `NDUFV1` (fold enrichment 40.66;
> adjusted P = 2.51×10^-4).”**

NetWeaver evaluated cumulative directed neighborhoods through three layers
and selected layer 3 for this candidate. The effective background contains
6,099 genes, of which 25 are in the AD-down mitochondrial query. Four of those
25 occur in the 24-gene `RPL13` neighborhood:

- `COX4I1`, a complex IV subunit;
- `SLC25A3`, the mitochondrial phosphate carrier;
- `ATP5F1B`, an ATP-synthase subunit; and
- `NDUFV1`, a complex I subunit.

The reported fold enrichment follows:

```text
observed neighborhood frequency = 4 / 24
background query frequency      = 25 / 6099

fold enrichment = (4 / 24) / (25 / 6099)
                ≈ 40.66
```

The adjusted P value is the Benjamini–Hochberg-corrected value after comparing
candidate drivers within that run. It shows that the overlap is unlikely under
the run's hypergeometric null, subject to the network, query, layer-selection,
and multiple-testing assumptions.

> **“This is the most defensible RPL13-specific signal behind the figure, but
> it is one primary directional context in one fixed astrocyte network.”**

It is “most defensible” because `RPL13` is not counted among the four overlap
genes. It is not conclusive because a single network and context cannot show
replication, the network edges do not have activating/inhibitory signs, and a
ribosomal candidate could mark general biosynthetic or stress-related
connectivity rather than selective mitochondrial regulation.

## 7. Prior work and interpretation, sentence by sentence

> **“Phase 09 annotated measured `RPL13` as a MitoCarta gene through a
> `unique_synonym` match to `MRPL13`.”**

The exact astrocyte annotation record is:

| Field | Recorded value |
|---|---|
| Measured feature | `RPL13` |
| GENCODE gene ID | `ENSG00000167526` |
| GENCODE gene name | `RPL13` |
| GENCODE match | `symbol` |
| MitoCarta symbol | `MRPL13` |
| MitoCarta match | `unique_synonym` |
| Classified as MitoCarta | `TRUE` |

The record is internally informative: gene identity stays `RPL13`, while the
mitochondrial classification comes from `MRPL13`. That mismatch is what must
be corrected.

> **“These are distinct official genes: NCBI describes [RPL13 (Gene ID
> 6137)](https://www.ncbi.nlm.nih.gov/gene/6137) as a cytoplasmic 60S
> ribosomal protein and [MRPL13 (Gene ID
> 28998)](https://www.ncbi.nlm.nih.gov/gene/28998) as a protein of the
> mitochondrial 39S large ribosomal subunit.”**

The local tested-gene table independently resolves both measured features:

| Gene | Ensembl ID | Chromosome | MitoCarta mapping |
|---|---|---|---|
| `RPL13` | `ENSG00000167526` | chr16 | incorrectly reaches `MRPL13` by synonym |
| `MRPL13` | `ENSG00000172172` | chr8 | canonical `MRPL13` match |

The shared “L13” wording describes the position of each protein in a different
ribosome. It does not make the genes orthologs, aliases that can be collapsed,
or interchangeable assay features.

> **“A synonym match that crosses those records can incorrectly admit RPL13
> to a mitochondrial query, making candidate-self enrichment especially
> easy.”**

KDA asks whether query genes are concentrated in a candidate's directed
neighborhood. If a candidate is wrongly added to the query and its
neighborhood contains itself, one overlap is present before any other
mitochondrial relationship is considered. This is especially influential for
the `Ast CHI3L1` example, where the result captures only two of six query
genes—`RPL13` and `FKBP8`. Half of the observed overlap is therefore the
candidate itself.

The correct remedy is not to relabel the output after testing. The query must
be rebuilt, the candidate layers retested, the best layer reselected, and the
within-run adjusted P values recomputed.

> **“This annotation problem does not automatically disqualify RPL13 as a
> *network candidate*: KDA candidates may be non-mitochondrial genes whose
> downstream neighborhoods are enriched for a mitochondrial query.”**

This is the most important conceptual distinction in the section:

```text
Role 1: query member
Question: Is RPL13 itself a validated mitochondrial signature gene?
Current answer: no; its membership is produced by the MRPL13 alias collision.

Role 2: network candidate
Question: Does an RPL13-centered neighborhood contain other, correctly
          annotated mitochondrial query genes more often than expected?
Current answer: possibly in Ast DPP10, but it requires a corrected rerun.
```

Many biologically plausible regulators of mitochondria are not located in
mitochondria. A transcription factor, signaling protein, cytoplasmic ribosomal
protein, or stress regulator can therefore be a valid KDA candidate while
remaining absent from the mitochondrial query.

> **“The targeted review found no primary study establishing the specific
> RPL13-to-OXPHOS relationship in AD astrocytes.”**

Prior biological plausibility is therefore indirect. The computational row
does not arrive with an established mechanism showing that changing RPL13 in
an AD-relevant astrocyte alters the four nominated OXPHOS genes or respiratory
function. Absence of a located study is not proof that no relationship exists,
but it prevents the network edge from being described as known biology.

## 8. Limits and decisive test, sentence by sentence

> **“Replace synonym-only gene matching with stable gene identifiers,
> distinguish `RPL13` from `MRPL13`, and rerun the affected Phase 09 signatures
> and Phase 12 enrichments.”**

A defensible repair should:

1. use Ensembl, NCBI Gene, or HGNC IDs as the primary identity key;
2. use symbols and synonyms only as controlled fallbacks;
3. reject or quarantine an alias when it is the current official symbol of a
   different gene;
4. rebuild the Phase 09 mitochondrial classification and direction-specific
   signatures;
5. identify every Phase 12 run whose query changes;
6. rerun layer selection, enrichment tests, and within-run adjustment;
7. regenerate the candidate summary and circular figure; and
8. audit other synonym-only MitoCarta matches for the same collision pattern.

This workflow matters because the error is upstream of the displayed figure.
Editing the label or deleting `RPL13` from the plot would hide the symptom
without correcting the analyses that produced it.

> **“RPL13 should be removed from the mitochondrial query unless its own
> identifier has independent mitochondrial evidence, while remaining eligible
> as a non-mitochondrial network candidate.”**

The default corrected state is:

```text
RPL13 in mitochondrial signature: no
RPL13 eligible as a network candidate: yes, if present in the network and
                                       tested background
MRPL13 in mitochondrial signature: yes, when MRPL13 itself is measured and
                                   directionally significant
```

This preserves the intended purpose of KDA: finding candidate regulators
whose neighborhoods are enriched for a biologically defined query, regardless
of whether the candidate belongs to that query.

> **“Then reassess the self-independent `Ast DPP10` result with expression-,
> degree-, and ribosomal-status-matched nulls and an independently inferred
> astrocyte network.”**

Each control addresses a different alternative explanation:

- **Expression matching** asks whether highly measured genes are more likely
  to acquire stable network neighborhoods and significant results.
- **Degree matching** asks whether RPL13 looks important mainly because it has
  many directed connections.
- **Ribosomal-status matching** compares RPL13 with other cytoplasmic
  ribosomal genes, which may share broad housekeeping or stress topology.
- **An independent network** tests whether the 24-gene neighborhood is robust
  to the particular data and network-inference procedure used here.

The hypothesis strengthens only if RPL13 outperforms these appropriate
comparators and the four-gene mitochondrial relationship recurs in another
network.

> **“Perturbation is justified only if a corrected,
> candidate-self-independent relationship survives those tests.”**

The proposed evidence sequence is deliberately gated:

```text
correct gene identities
        ↓
rerun mitochondrial signatures and KDA
        ↓
retain a self-independent RPL13 neighborhood
        ↓
beat expression/degree/ribosomal matched nulls
        ↓
reproduce in an independent astrocyte network
        ↓
perform perturbation, rescue, and functional assays
```

If it reaches the experimental stage, bidirectional RPL13 perturbation should
measure the four nominated genes at RNA and protein levels, respiratory-chain
assembly, ATP-linked and maximal respiration, ATP, membrane potential, and
ROS. Rescue and general-translation, stress, viability, and cell-death
controls are necessary to distinguish a selective mitochondrial effect from
global ribosomal dysfunction or toxicity.

## 9. How to interpret the corrected outcomes

| Corrected outcome | Interpretation |
|---|---|
| RPL13 disappears from all significant rows | The displayed recurrence was primarily an annotation-enabled artifact. |
| Only the primary `Ast DPP10` directional row and reused derivatives remain | A narrow, low-confidence candidate hypothesis survives; this is not broad astrocyte recurrence. |
| Several self-independent contexts remain after matched nulls | Computational support strengthens, but shared networks and observational data still limit causality. |
| The relationship reproduces in an independent astrocyte network | The topology is less likely to be specific to one inferred network. |
| RPL13 perturbation selectively changes the nominated OXPHOS panel and respiration, with rescue | A mechanistic RPL13-to-mitochondrial hypothesis gains experimental support. |
| Effects appear only with translation collapse, stress, or cell death | A nonspecific ribosomal-stress explanation is favored. |

## 10. Safe and unsafe claims

Safe claims include:

- `RPL13` is fifth among the five displayed Astrocytes-network candidates
  under the figure's descriptive ranking rule.
- Seventeen of 21 displayed rows contain candidate-self overlap.
- One primary directional `Ast DPP10` row is self-independent and covers four
  other mitochondrial query genes.
- `RPL13` and `MRPL13` are distinct genes, and the current synonym mapping
  requires correction.
- A non-mitochondrial gene can remain eligible as a KDA candidate.

Unsafe claims include:

- “RPL13 is a MitoCarta mitochondrial ribosomal protein.”
- “Twenty-one independent analyses validate RPL13.”
- “A 128.57-fold expression change supports RPL13.”
- “Nineteen global calls make RPL13 universal across astrocytes.”
- “The current adjusted P values remain valid after simply deleting RPL13
  from the overlap lists.”
- “RPL13 regulates OXPHOS in AD astrocytes.”

## 11. One-sentence takeaway

Most astrocytic `RPL13` recurrence is inseparable from an erroneous
`RPL13`-to-`MRPL13` mitochondrial-query assignment, while one
candidate-self-independent `Ast DPP10` result leaves a narrow network
hypothesis that should advance only after identifier-based reannotation,
complete rerunning, matched-null testing, and independent-network replication.
