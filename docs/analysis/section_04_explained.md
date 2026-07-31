# Tutorial: understanding Section 4, “Positive mitochondrial similarity mostly represents shared below-threshold response”

**Source section:** [Joint Phase 11–12 synthesis](phase11_phase12_joint_mitochondrial_discussion.md)  
**Audience:** readers who want to understand what the Phase 10 similarity score does—and does not—mean  
**Purpose:** explain why a positive similarity score should not automatically be called shared biological activation

## 1. The central idea

The similarity analysis first reduced each gene–cell-type result to one of
three values: `+1` for significantly AD-up, `-1` for significantly AD-down,
and `0` for not passing the study's thresholds. Two profiles often receive a
positive similarity contribution because both contain `0`. In the high
similarity tails, 97%–99% of contributing state pairs are `(0,0)`. Therefore,
“high similarity” mostly means **neither comparison crossed the DEG threshold**,
not “both comparisons strongly activated the pathway.”

## 2. Vocabulary

| Term | Meaning |
|---|---|
| **Threshold-level DEG** | A result that passes both the fold-change and false-discovery criteria. |
| **Thresholded state** | The simplified value `-1`, `0`, or `+1` assigned after applying those criteria. |
| **Comparator** | One of the profiles being compared, such as one sex/APOE stratum versus another. |
| **Similarity score** | A summary of how often two thresholded profiles agree or disagree. |
| **High tail** | Genes or pathways with the most positive similarity values. |
| **Low tail** | Genes or pathways with the most negative values. |
| **`(0,0)`** | Neither member of a paired comparison passes the DEG threshold. |
| **Continuous effect** | The original estimated change, such as log2 fold change, before it is collapsed to three states. |

## 3. The title explained

“Positive mitochondrial similarity” sounds as though both profiles show the
same strong response. The phrase “mostly represents shared below-threshold
response” corrects that interpretation. The word **below-threshold** is more
accurate than **unchanged**: a `0` can represent a true lack of effect, a small
effect, or an uncertain estimate.

The novelty label, **“new analytical clarification,”** means the discovery is
about how this study's encoding behaves. It is not a newly discovered
mitochondrial mechanism.

## 4. Discovery sentence

> **“The most positive Phase 10 mitochondrial similarity scores and their
> apparent pathway enrichments are driven overwhelmingly by gene–cell-type
> pairs with no threshold-level DEG in either comparator.”**

Suppose a gene has a modest positive estimated change in one profile and a
modest negative estimate in another, but neither passes the thresholds. Both
are encoded as `0`, producing the pair `(0,0)`. A gene with essentially no
change in either profile is also `(0,0)`. The thresholded analysis cannot tell
these situations apart.

“Driven overwhelmingly” is supported by the 97%–99% figure in the evidence
paragraph. “Apparent pathway enrichments” means some named pathways occur
often in the high tail, but the state pairs underlying that enrichment must be
examined before giving it a biological direction.

## 5. Conclusion sentences

> **“‘High similarity’ should be interpreted as relative stability or shared
> absence of threshold-level change, not shared activation or repression.”**

The safe conclusion is:

- both profiles usually failed to produce a threshold-level change for the
  same gene–cell-type pairs.

The unsafe conclusions are:

- both profiles activated the pathway;
- both profiles suppressed the pathway; or
- the pathway is biologically inactive.

> **“This clarification prevents a publishable pathway figure from being
> described more strongly than its underlying states allow.”**

A figure caption should say “high similarity dominated by paired
below-threshold states.” It should not say “concordant upregulation” unless the
underlying pairs are actually `(+1,+1)`, or “concordant downregulation” unless
they are `(-1,-1)`.

## 6. Data-driven evidence

> **“None of the positive similarity scores is gene-level significant.”**

The positive ranking does not come with statistically significant individual
genes. This weakens any claim that a particular gene is robustly concordant.

> **“For pathways appearing in the high tails, including TCA-cycle and
> import/homeostasis annotations, 97%–99% of contributing paired states are
> `(0,0)`.”**

Out of 100 contributing pairs, roughly 97 to 99 have no threshold-level DEG on
either side. Only about 1 to 3 pairs have some other state combination. Thus,
the pathway name may be enriched, but the enrichment is almost entirely an
enrichment of shared zeros.

> **“By contrast, the low tails contain the recurrent OXPHOS concentration
> described above.”**

The negative side of the analysis contains many OXPHOS genes whose directions
differ across profiles. That low-tail signal is qualitatively different from
the high-tail `(0,0)` signal.

## 7. Why this does not require a biological literature citation

This result follows from the study's own coding rules. The relevant “prior
work” is the transformation:

| Original possibilities | Thresholded code |
|---|---:|
| clear significant increase | `+1` |
| clear significant decrease | `-1` |
| tiny effect | `0` |
| noisy or underpowered effect | `0` |
| genuine absence of change | `0` |

Because several different realities collapse to `0`, `(0,0)` is ambiguous.
An outside experiment cannot resolve that mathematical ambiguity; the
analysis must retain more of the original information.

## 8. The decisive reanalysis

The source proposes two improvements:

1. **Donor-aware continuous estimates.** Compare the actual fold-change
   estimates and their uncertainty, while treating each donor—not each
   nucleus—as the biological replicate.
2. **Direction-aware ranked gene-set tests.** Rank genes by signed continuous
   evidence and ask whether a pathway accumulates toward the positive or
   negative end without converting everything to `-1/0/+1`.

These methods can distinguish small shared increases, small shared decreases,
opposite weak changes, and genuine stability.

## 9. How to phrase the current result

Supported:

- “The high-similarity tail is dominated by paired below-threshold states.”
- “These pathways are relatively stable under the thresholded encoding.”
- “Continuous-effect analysis is required to determine weak concordance.”

Not supported:

- “The TCA cycle is jointly activated.”
- “Import/homeostasis genes are jointly repressed.”
- “A zero proves no biological change.”

## 10. One-sentence takeaway

The positive similarity result mostly says “both sides were coded zero,” so it
should be described as shared below-threshold behavior until continuous,
donor-aware analyses show whether the underlying effects truly agree.
