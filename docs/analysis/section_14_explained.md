# Tutorial: understanding Section 14, “RPS15 is a recurrent cross-network candidate”

**Source section:** [Joint Phase 11–12 synthesis](phase11_phase12_joint_mitochondrial_discussion.md)  
**Audience:** readers who want to compare RPS15 with the stronger RPL11 nomination  
**Purpose:** explain why RPS15 is a new but second-tier mitochondrial-network candidate

## 1. The central idea

`RPS15` is another cytosolic ribosomal protein. Phase 12 repeatedly nominates
it in mitochondrial-query networks, and its primary calls do not depend on
RPS15 being in the input query. However, it is much less often the most
upstream nonredundant candidate than RPL11. Prior studies connect RPS15 to p53
and Parkinsonian neuronal stress, but there is no direct AD perturbation study
supporting the exact mitochondrial network proposed here.

## 2. Vocabulary

| Term | Meaning |
|---|---|
| **RPS15** | A protein of the small subunit of cytosolic ribosomes. |
| **Cross-network candidate** | A gene nominated in several separately analyzed networks. |
| **Primary call** | A directional or union KDA row retained as a primary result rather than a secondary summary. |
| **Global call** | A call in which the candidate remains the most upstream nonredundant representative. |
| **Ribosomal-hub risk** | The possibility that a broadly expressed, highly connected ribosomal gene recurs for general network reasons. |
| **LRRK2** | A kinase linked to inherited and sporadic Parkinson's disease biology. |
| **Phosphorylation** | Addition of a phosphate group that can alter a protein's activity or interactions. |

## 3. Discovery sentence

> **“`RPS15` is a recurrent Phase 12 candidate across five networks, and every
> primary call is candidate-self-independent; it is much less often the most
> upstream nonredundant candidate than `RPL11`.”**

The first half is favorable: breadth across networks plus self-independence
reduces concern that RPS15 was nominated only because it appeared in the query.
The second half lowers its priority: most RPS15 calls do not survive as global
representatives when redundant upstream candidates are resolved.

## 4. Conclusion sentences

> **“The exact RPS15-to-mitochondrial AD topology is new.”**

The targeted literature review did not find the same RPS15-centered human AD
mitochondrial network.

> **“Prior p53 and Parkinsonian stress biology makes it plausible, but the low
> global fraction and ribosomal-hub risk place it below RPL11 for mechanistic
> testing.”**

Plausibility is not confirmation. RPS15 can influence stress and survival, so
a mitochondrial effect is biologically possible. Yet a limited experimental
budget should prioritize RPL11 first because its global fraction is much
higher and its specific Phase 11 candidate links are better characterized.

## 5. Evidence, item by item

- 123 total calls
- 50 primary calls
- five networks
- 22 fine cell types
- 26 conservative directional calls across 19 fine types
- minimum within-run adjusted P as small as `4.57 × 10^-14`
- every primary call candidate-self-independent
- up to 19 query genes covered by one neighborhood

These numbers show breadth and strong within-run enrichment. They do not tell
us whether the same biological effect replicated in independent cohorts.

Only 23 of 123 calls are global:

`23 / 123 = 18.7%`

For RPL11, 118 of 131 are global:

`118 / 131 = 90.1%`

The comparison does not say RPS15 is false. It says RPL11 much more often
occupies the nonredundant upstream position defined by this KDA.

## 6. Prior work

RPS15 can bind and inhibit MDM2, stabilize p53, and promote arrest or death in
non-neural models
([Daftuar et al., 2013](https://doi.org/10.1371/journal.pone.0068667)).
LRRK2-dependent phosphorylation of RPS15 contributed to neuronal toxicity in
Parkinsonian models
([Martin et al., 2014](https://doi.org/10.1016/j.cell.2014.01.064)).

These papers establish stress-related possibilities. Parkinson's disease is
not Alzheimer's disease, and neither study validates a selective
RPS15-to-mitochondrial AD mechanism. The targeted review found no primary
AD-specific RPS15 perturbation study.

## 7. Limits and decisive test

RPS15 should undergo the same safeguards as RPL11:

1. compare it with genes matched for expression, network degree, and
   ribosomal status;
2. repeat nomination in an independently inferred network;
3. rerun KDA with candidate exclusion;
4. perturb RPS15 within a narrow range that avoids catastrophic ribosome
   failure.

Every experiment should measure general translation, p53, arrest, viability,
and death at the same time as mitochondrial RNA, proteins, respiration, and
quality control. If mitochondrial changes appear only after translation
collapses or cells begin dying, general ribosomal toxicity is a better
explanation than selective mitochondrial regulation.

## 8. How to rank the result

Supported:

- RPS15 is a recurrent, self-independent computational candidate.
- Its exact AD mitochondrial topology appears new.
- It deserves matched-null validation and possibly second-stage testing.

Not supported:

- RPS15 is an established AD driver.
- RPS15 selectively controls mitochondria.
- RPS15 is stronger than RPL11.
- A Parkinson's model independently confirms the AD result.

## 9. One-sentence takeaway

RPS15 is a broad and statistically strong new network candidate, but its low
global fraction and generic ribosomal-stress risk make it a lower mechanistic
priority than RPL11.
