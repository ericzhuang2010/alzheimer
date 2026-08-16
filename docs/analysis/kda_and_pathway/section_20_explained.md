# Tutorial: understanding Section 20, “The mitochondrial-localized Phase 11 shortlist is mainly a candidate mediator/readout panel”

**Source section:** [Joint Phase 11–12 synthesis](phase11_phase12_joint_mitochondrial_discussion.md)  
**Audience:** readers who want to understand how Phase 12 changes—not discards—the Phase 11 shortlist  
**Purpose:** explain the proposed upstream-candidate, mediator, and readout hierarchy

## 1. The central idea

Phase 11 identified mitochondrial genes that repeatedly changed with AD in
particular cells and strata. Phase 12 often places those genes inside
neighborhoods centered on signaling, stress, chromatin, or other
non-mitochondrial candidates. The joint interpretation is that many original
genes may be **mediators** carrying an upstream signal or **readouts** showing
that mitochondrial function changed. This is a revised experimental role, not
a claim that the original shortlist was wrong.

## 2. Vocabulary

| Term | Meaning |
|---|---|
| **Upstream candidate** | A gene computationally placed earlier in a proposed regulatory hierarchy. |
| **Mediator** | A molecule through which an upstream candidate produces a downstream effect. |
| **Readout** | A measurable indicator that a biological process changed. |
| **Pharmacodynamic readout** | A measurement used to show that an intervention affected its intended biological pathway. |
| **Prespecified** | Chosen before an experiment is evaluated, reducing the temptation to select only favorable outcomes afterward. |
| **Epistasis** | Experimental testing of whether one gene's effect depends on another gene. |
| **Rescue** | Restoration of a disrupted outcome by returning a gene or pathway toward normal. |
| **Derived union** | A combined `AD_both_mito` query based on directional signatures; it is not an independent biological repeat. |

## 3. Discovery and conclusion

> **“Phase 12 frequently positions the mitochondrial-localized Phase 11
> candidates beneath newly nominated signaling, stress, or
> non-mitochondrial candidates.”**

“Beneath” refers to the inferred network hierarchy. It does not prove a
molecular direction, because KDA lacks activating/inhibitory signs and is not
a perturbation experiment.

> **“The earlier genes remain experimentally valuable, but their best joint
> use is now as prespecified candidate mediators and pharmacodynamic readouts
> for upstream-candidate perturbations.”**

Instead of testing only whether ATP5IF1 or TUFM is an upstream cause, an
experiment can perturb LAMTOR5 or APOE and ask in advance whether ATP5IF1 or
TUFM responds. Then it can test whether blocking or restoring the mitochondrial
gene changes the functional outcome.

> **“This conclusion applies to the mitochondrial-localized portion of the
> shortlist; the nuclear biogenesis candidates in Section 19 remain
> unresolved.”**

The revised role is not automatically assigned to PPARGC1A, PPARGC1B, or
SMARCD3, because Phase 12 did not place those genes under another candidate.

## 4. The table, row by row

### ATP5IF1 below LAMTOR5

There are 28 primary pair calls: 15 directional and 13 derived unions across
11 fine types. This is the broadest exact candidate–mediator pairing in the
table. Proposed use: ATP5IF1 as an ATP-synthase mediator/readout after
LAMTOR5/nutrient-sensing perturbation.

### TUFM below astrocytic APOE

All seven primary APOE astrocyte neighborhoods contain TUFM: four directional
and three unions. The exact Ast GRM3 ε2 reversal makes TUFM a prespecified
mitochondrial-translation response to measure after APOE perturbation.

### TOMM7 below RPL11

Four primary pair calls comprise two directional and two unions. TOMM7 should
remain a direct mitophagy/import candidate because prior work establishes its
role in PINK1 stabilization, but the joint topology suggests also measuring it
as a downstream response to ribosomal stress.

### HSPD1 below HSPA1A

HSPD1 occurs in all ten primary HSPA1A neighborhoods: five directional and
five unions. It is a proposed mitochondrial-proteostasis readout. Because both
genes could respond to common stress, mediation is lower confidence.

### PARK7 below GABARAPL2

Sixteen primary pair calls—nine directional and seven unions—place PARK7 in a
quality-control neighborhood. PARK7 becomes a candidate mediator to block or
rescue after GABARAPL2 manipulation.

### ATP5IF1, FIS1, and PARK7 below OPC FTL or ANKRD11

For each candidate–readout pair, there are two primary calls: one directional
and one union. The small count supports a panel rather than a separate strong
mechanism for every gene. Together the genes monitor ATP synthase,
mitochondrial division, and stress/mitophagy responses to OPC iron or chromatin
perturbation.

### APOO below RPL11

APOO has 15 primary pair calls: eight directional and seven unions. It is the
most recurrent RPL11 mitochondrial bridge and can report inner-membrane/cristae
responses.

### SLIRP below RPL11

SLIRP has two primary pair calls: one directional and one union. It is a
lower-evidence mtRNA-maintenance readout, not an independently replicated
mechanism.

## 5. Why the candidate summaries support revised roles

> **“The derived `AD_both_mito` rows reuse directional-signature genes and are
> not independent confirmations.”**

A union row is built from existing direction-specific inputs. It adds a useful
combined view, not a new cohort or experiment.

> **“`ATP5IF1` is absent from the KDA candidate summary.”**

ATP5IF1 is recurrent as a Phase 11 DEG and as a gene inside LAMTOR5
neighborhoods, but it was not selected as a Phase 12 upstream candidate. That
pattern is compatible with a mediator/readout role.

> **“`TUFM` has 39 KDA calls but is always a query member and never global.”**

TUFM's own candidacy is vulnerable to self-membership and it never survives as
the nonredundant upstream representative. In contrast, its occurrence below
self-independent APOE is more informative for hierarchy.

> **“`TOMM7` has eight calls whose primary evidence is
> candidate-self-containing and narrow.”**

TOMM7 remains functionally important, but its Phase 12 upstream nomination is
not clean enough to outrank RPL11.

> **“`PARK7` has six calls, three primary calls, only one
> candidate-self-independent primary call, and no call passing the
> conservative directional screen.”**

PARK7's direct candidate evidence is weak compared with its repeated presence
inside GABARAPL2 neighborhoods.

> **“These features favor mediator/readout roles without proving them.”**

Network location generates the revised hypothesis. Only epistasis experiments
can distinguish mediator, parallel response, and passive readout.

## 6. Prior work and interpretation

Sections 6–8 and 13 of the [joint synthesis](phase11_phase12_joint_mitochondrial_discussion.md)
review direct experimental literature for TUFM, ATP5IF1, TOMM7, PARK7, APOO,
SLIRP, and related candidates. Their known mitochondrial functions remain
important. Phase 12 changes their proposed **location** in an experimental
hierarchy; it does not erase Phase 11 recurrence or prior functional evidence.

## 7. The decisive experimental logic

For each pair:

1. perturb the proposed upstream candidate;
2. require coherent changes in several prespecified downstream genes and a
   mitochondrial functional measurement;
3. perturb the proposed mediator alone;
4. block or restore the mediator during upstream-candidate perturbation.

Example:

`LAMTOR5 perturbation → ATP5IF1 change → ATP-synthase/respiration change`

If ATP5IF1 rescue restores mitochondrial function while LAMTOR5 remains
perturbed, mediation is supported. If ATP5IF1 changes but its rescue does not
affect function, it is more likely a readout. If it does not change at all, the
proposed hierarchy is weakened.

## 8. One-sentence takeaway

Phase 12 does not discard the Phase 11 mitochondrial shortlist; it turns much
of it into a prespecified panel for testing whether new upstream candidates
act through—or merely alter—mitochondrial mediators and readouts.
