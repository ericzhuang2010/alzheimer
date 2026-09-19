#!/usr/bin/env python3
"""Synchronize speaker notes with the reviewed 2026-09-16 slide order.

The presentation was manually reorganized after its analysis slides were
generated.  This utility treats the reviewed 160-slide deck as authoritative,
updates notes for the DEG, pathway, and finding additions, and rewrites transitions so
that they point to the slide that now follows.  Slide content and ordering are
intentionally left unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import tempfile
from pathlib import Path

from pptx import Presentation

from append_09162026_remaining_findings import (
    NEW_SLIDE_TITLES,
    NEW_SLIDE_TRANSITIONS,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DECK = (
    ROOT
    / "docs"
    / "presentations"
    / "09162026"
    / "09162026_sex_apoe_kda_fine_broad.pptx"
)
AUDIT_ROOT = ROOT / "results" / "presentations" / "09162026_speaker_notes"

BASE_EXPECTED_TITLES = (
    "Sex, APOE, and Mitochondrial Gene Expression in Alzheimer’s Disease --Eric Zhuang",
    "DEG Analysis",
    "What is a contrast",
    "Overall DEG counts vary across sex/APOE groups",
    "Pathway analysis",
    "Three levels of MitoCarta pathways",
    "How the pathway analysis was done",
    "Four mitochondrial pathways highlighted",
    "How to calculate pathway and sex/APOE overlap",
    "Which pathway genes appeared among the DEGs?",
    "How the upregulated occurrence percentage is calculated",
    "Share of OXPHOS DEG occurrences that are upregulated",
    "PART 3",
    "What is a category",
    "Four steps: run DEG per contrast, one KDA query per contrast",
    "Summary for ROSMAP",
    "54 fine cell types create 324 planned contrasts",
    "Source validity and query size decide whether KDA is called",
    "Mitochondrial query genes",
    "ROSMAP KDA summary: 381 non-MT gene x category combinations represent 228 distinct genes",
    "RPS15 recurs across 11 returned-only categories",
    "Top five: 123 non-MT entries across 29 categories",
    "ROSMAP excitatory-neuron drivers recur across sex/APOE groups",
    "ROSMAP inhibitory-neuron drivers recur across sex/APOE groups",
    "ROSMAP astrocyte drivers recur across sex/APOE groups",
    "ROSMAP OPC drivers recur across sex/APOE groups",
    "PART 4",
    "Summary for SEA-AD",
    "129 SEA-AD supertypes create 774 planned contrasts",
    "SEA-AD KDA summary: 44 non-MT gene x category combinations represent 43 distinct genes",
    "PJVK is the only gene recurring across 2 SEA-AD categories",
    "Top-five display: 17 non-MT entries across 5 categories",
    "SEA-AD excitatory-neuron drivers occur in two sex/APOE groups",
    "PART 4",
    "Donor-threshold sensitivity — numerical comparison",
    "Donor-threshold sensitivity — key findings",
    "Query-size sensitivity — numerical comparison",
    "Query-size sensitivity — cohort effects",
    "Query-size sensitivity — validation interpretation",
    "Findings and discussions",
    "FINDING 1",
    "Female ε3/ε3 cells (especially excitatory neurons) raise mtDNA energy-gene RNA in AD",
    "ROSMAP: the female ε3/ε3 mtDNA-OXPHOS signal is consistently AD-up",
    "SEA-AD adds narrow but strong support for the excitatory-neuron program",
    "Why this matters: excitatory neurons may be mounting a coordinated mitochondrial response",
    "What the finding does not prove—and the next evidence needed",
    "Prior research makes the result plausible—but does not duplicate it",
    "FINDING 2",
    "Male ε3/ε3 cells raise mtDNA energy-gene RNA while lowering nuclear energy-gene RNA",
    "ROSMAP: male ε3/ε3 cells show opposite OXPHOS RNA directions",
    "SEA-AD supports the matched male ε3/ε3 inhibitory-neuron program",
    "Which genes carry the matched inhibitory-neuron signal?",
    "Why this matters: one respiratory system depends on two genomes",
    "What the finding does not prove—and the next evidence needed",
    "Prior research supports the ingredients—but not this exact mismatch",
)

BASE_TRANSITIONS = (
    "Begin with the DEG analysis and define the comparison unit.",
    "Start by defining a contrast, the unit used for each AD-versus-comparison DEG analysis.",
    "With the contrast defined, summarize all significant DEG results across sex/APOE groups.",
    "Move from the all-gene DEG counts to pathway analysis.",
    "Introduce the three-level MitoCarta hierarchy used to define the pathway sets.",
    "Explain how the pathway analysis was performed and show the breadth of the pathway search.",
    "Focus next on four mitochondrial pathways used repeatedly in the later findings.",
    "Explain how fine-cell DEG results are pooled into each overlap value.",
    "Inspect which genes in those pathways appeared among the DEGs.",
    "Define how the OXPHOS upregulated occurrence percentage is calculated.",
    "Compare the upregulated occurrence percentage across the six sex/APOE groups.",
    "Now move to Part 3, where mitochondrial DEGs become network-analysis queries.",
    "Before walking through KDA, define the category used to summarize fine-cell results.",
    "With categories defined, follow one contrast from DEG analysis to its category-level KDA result.",
    "Summarize the ROSMAP branch before examining its contrast funnel.",
    "Follow the ROSMAP summary into the contrast-level funnel.",
    "Clarify the execution gate and the source contrasts that could not be fitted.",
    "Inspect how the mitochondrial query is constructed.",
    "Summarize the returned non-mitochondrial KDA results before examining rankings and recurrence.",
    "Start with the most recurrent ROSMAP drivers.",
    "Then inspect the ranked top-five display across the 29 populated categories.",
    "Next, view recurrence within each broad cell class, beginning with excitatory neurons.",
    "Compare the excitatory-neuron pattern with inhibitory neurons.",
    "Compare the inhibitory-neuron pattern with astrocytes.",
    "Compare the astrocyte pattern with OPCs.",
    "Move to the SEA-AD validation branch.",
    "Summarize SEA-AD coverage before examining its contrast funnel.",
    "Follow the SEA-AD summary into the contrast-level funnel.",
    "Summarize the returned non-mitochondrial SEA-AD output.",
    "Then examine recurrence across SEA-AD categories.",
    "Inspect the top-five entries in the five populated SEA-AD categories.",
    "Finish the SEA-AD branch with excitatory-neuron recurrence across groups.",
    "Move to the sensitivity analyses.",
    "Begin with the numerical consequences of changing the donor threshold.",
    "Interpret why the two cohorts respond differently to the donor threshold.",
    "Continue with sensitivity to the minimum effective mitochondrial-query size.",
    "Identify the calls responsible for the query-size step changes.",
    "Finish with the implications for matched-stratum validation.",
    "Turn from robustness checks to the main biological findings and their interpretation.",
    "Begin with Finding 1, the female ε3/ε3 mtDNA-OXPHOS increase.",
    "State the first finding in plain language.",
    "Show the ROSMAP numbers behind the statement.",
    "Ask whether the same excitatory-neuron program appears in SEA-AD.",
    "Explain why a repeated mitochondrial program may matter biologically.",
    "Separate the observation from what still needs to be tested.",
    "Place the first finding in prior research.",
    "Proceed to Finding 2, the male ε3/ε3 mitonuclear mismatch.",
    "State the second finding in plain language.",
    "Show the ROSMAP numbers behind the mismatch.",
    "Ask whether the matched inhibitory-neuron program appears in SEA-AD.",
    "Show which genes carry the cross-cohort directional agreement.",
    "Explain why opposite directions across two genomes may matter.",
    "Separate the observation from what still needs to be tested.",
    "Place the second finding in prior research.",
    "Close by emphasizing the testable biological hypotheses and the limits of transcript-level evidence.",
)

EXPECTED_TITLES = BASE_EXPECTED_TITLES + NEW_SLIDE_TITLES
TRANSITIONS = (
    BASE_TRANSITIONS[:-1]
    + ("Proceed to Finding 3, the coordinated female ε2 OXPHOS increase.",)
    + NEW_SLIDE_TRANSITIONS
)

_PRE_OVERLAP_INSERT_NOTE_OVERRIDES = {
    1: {
        "goal": "Introduce the research question and presentation scope.",
        "walkthrough": (
            "This study asks how sex, APOE genotype, and brain cell type shape "
            "mitochondrial gene-expression changes in Alzheimer’s disease. ROSMAP "
            "provides the primary analysis, and SEA-AD provides supplemental human "
            "support. The presentation moves from DEG and pathway framing to KDA, "
            "sensitivity analyses, and 17 biological findings."
        ),
        "boundary": (
            "The evidence is transcriptomic and exploratory. Separate results within "
            "sex/APOE strata do not by themselves establish a disease-by-sex or "
            "disease-by-APOE interaction, and RNA abundance does not measure "
            "mitochondrial function directly."
        ),
    },
    2: {
        "goal": "Introduce the differential-expression layer.",
        "walkthrough": (
            "DEG analysis compares disease with the cohort-specific comparison group "
            "inside each fine cell type and sex/APOE stratum. These contrast-level "
            "results provide the mitochondrial gene lists used for pathway analysis "
            "and for the KDA queries."
        ),
        "boundary": (
            "A DEG is an RNA-abundance difference, not proof of causal regulation, "
            "protein change, or altered mitochondrial function. ROSMAP uses AD versus "
            "NCI, whereas SEA-AD uses dementia versus no dementia."
        ),
    },
    3: {
        "goal": "Distinguish the contrast unit from the KDA call it may generate.",
        "walkthrough": (
            "A contrast is one AD-versus-NCI comparison within one fine cell type "
            "and one sex/APOE group. Therefore, N fine cell types create six N "
            "planned contrasts; in ROSMAP, 54 fine types create 324. Source-invalid "
            "contrasts are removed, and a valid contrast proceeds to "
            "call_key_drivers only when its mapped mitochondrial query contains at "
            "least three genes. One completed call can return a list of significant "
            "key-driver genes, with each gene appearing at most once in that call."
        ),
        "boundary": (
            "A planned contrast is a comparison opportunity, not a completed KDA "
            "test or an independent biological replication. A skipped contrast is "
            "unavailable rather than a completed null result."
        ),
    },
    4: {
        "goal": "Summarize the complete fine-cell DEG results before pathway analysis.",
        "walkthrough": (
            "ROSMAP contained 324 planned AD-versus-NCI contrasts: 54 fine cell "
            "types crossed with six sex/APOE groups. Three male epsilon-2 contrasts "
            "did not have enough cells for the planned DEG model, leaving 321 "
            "analyzed contrasts; 277 of those had "
            "at least one DEG. Across all genes, there were 118,297 significant "
            "gene-by-fine-cell comparison occurrences representing 14,840 distinct "
            "genes. The bars divide these occurrences into higher expression in AD "
            "and lower expression in AD. Female epsilon-2 had 10,952 occurrences, "
            "65 percent higher in "
            "AD. Female epsilon-3 homozygous had 11,236, 47 percent higher. Female "
            "epsilon-4 had 20,942, with 76 percent lower in AD. Male epsilon-2 had the "
            "largest count, 45,781, with 56 percent higher. Male epsilon-3 homozygous "
            "had 13,120, and male epsilon-4 had 16,266; both were close to evenly split."
        ),
        "boundary": (
            "A DEG met the prespecified within-contrast criteria: BH FDR below 0.05, "
            "absolute fold change above 1.3, and detection in at least 10 percent of "
            "cells in either group. Counts repeat a gene when it is significant in "
            "another fine-cell comparison. They are descriptive and can reflect "
            "sample size, power, and the number of genes tested; they are not donor "
            "counts, independent replications, or a formal disease-by-sex/APOE "
            "interaction test."
        ),
    },
    9: {
        "goal": (
            "Interpret OXPHOS DEG direction across sex/APOE groups and highlight the "
            "contrasting epsilon-3 homozygous patterns."
        ),
        "walkthrough": (
            "OXPHOS, or oxidative phosphorylation, is the mitochondrial process "
            "that produces most cellular ATP. Blue bars summarize the 13 OXPHOS "
            "genes encoded by mitochondrial DNA, and orange bars summarize 86 "
            "structural OXPHOS genes encoded by nuclear DNA. Every bar starts at the "
            "50 percent line, where upregulated and downregulated occurrences are "
            "equally common. Bars extend upward when more than half of the occurrences "
            "are upregulated and downward when fewer than half are upregulated. The "
            "label at the end of each bar gives the actual upregulated percentage, "
            "while bar length shows its percentage-point distance from 50 percent. "
            "The key contrast is shown in the callout. In female epsilon-3 homozygous, "
            "both gene sets are predominantly upregulated: 100 percent for the "
            "mitochondrial-DNA set and 85 percent for the nuclear-DNA set. In male "
            "epsilon-3 homozygous, the two sets diverge: 86 percent of mitochondrial-"
            "DNA occurrences are upregulated, but only 12 percent of nuclear-DNA "
            "occurrences are upregulated, which means 88 percent are downregulated. "
            "The broader pattern is that female epsilon-2 is predominantly upregulated "
            "in both sets, female epsilon-4 and male epsilon-2 are predominantly "
            "downregulated in both, and male epsilon-4 shows a weaker version of the "
            "male epsilon-3 homozygous split."
        ),
        "boundary": (
            "The bars show the share of repeated gene-by-fine-cell DEG occurrences "
            "that are upregulated. The vertical displacement from 50 percent is a "
            "descriptive percentage-point difference, not an effect size. The chart "
            "does not show percent expression change, percent of cells or donors, "
            "percent of unique genes, pathway enrichment, OXPHOS activity, or a direct "
            "statistical interaction between disease, sex, and APOE."
        ),
    },
    5: {
        "goal": "Position pathway analysis between DEG testing and network analysis.",
        "walkthrough": (
            "Pathway analysis asks whether mitochondrial DEG results are concentrated "
            "in predefined pathways, including mtDNA OXPHOS, nuclear OXPHOS, "
            "mitochondrial translation, and MICOS or inner-membrane organization. It "
            "therefore describes pathway-level signal before network-based driver "
            "nomination."
        ),
        "boundary": (
            "Pathway enrichment describes the composition or ranking of gene-level "
            "results. It does not identify an upstream driver or prove that a pathway "
            "is more or less functional."
        ),
    },
    6: {
        "goal": "Explain the two-stage pathway analysis and define a significant result.",
        "walkthrough": (
            "Each estimable fine-cell sex/APOE contrast was analyzed separately. For "
            "each contrast, the analysis created three mitochondrial DEG lists: all "
            "significant DEGs, genes up-regulated in AD, and genes down-regulated in "
            "AD. It then tested each pathway to ask whether the DEG list contained "
            "more pathway genes than expected among genes detectable in the same "
            "contrast. A significant result means that the greater-than-expected "
            "overlap remained significant after Benjamini-Hochberg correction across "
            "the pathways in the same collection for that DEG list, with a "
            "false-discovery rate below 5 percent. Twelve of the 46 Level 1 and Level "
            "2 pathways and 18 of the 149 complete pathways had at least one "
            "significant result. Most significant results involved overlapping "
            "OXPHOS pathways. Non-OXPHOS signals were fewer and more localized."
        ),
        "boundary": (
            "The complete 149-pathway collection contains the 46 Level 1 and Level 2 "
            "pathways, so the two reported scopes overlap. At least one significant "
            "result means enrichment in at least one fine-cell, sex/APOE, and DEG "
            "direction list. It does not mean significance in every group or prove "
            "altered pathway activity."
        ),
    },
    7: {
        "goal": "Introduce the four mitochondrial pathways highlighted in the focused results.",
        "walkthrough": (
            "The focused analysis highlights four fixed pathway definitions, using "
            "the same gene membership in every contrast. The first contains the 13 "
            "OXPHOS subunits encoded by mitochondrial DNA. The second contains 86 "
            "structural OXPHOS subunits encoded by nuclear DNA. The third contains "
            "155 genes involved in translating proteins inside mitochondria. The "
            "fourth contains 19 MIB/MICOS genes that organize the inner mitochondrial "
            "membrane and its folds, called cristae."
        ),
        "boundary": (
            "These are focused benchmark pathways, not the full pathway search. Phase "
            "11 also tested 46 Level 1 and Level 2 MitoCarta pathway categories and "
            "all 149 MitoCarta pathways. Listing a pathway, or observing some of its "
            "genes among the DEGs, does not establish enrichment or altered function."
        ),
    },
    8: {
        "goal": "Show the breadth of pathway-gene overlap with the fine-cell DEG results.",
        "walkthrough": (
            "For each sex/APOE group, a pathway gene is counted once if it was a "
            "significant DEG in at least one fine-cell comparison. The denominator is "
            "the full frozen pathway size shown on the previous slide. Twelve of the "
            "13 mitochondrial-DNA OXPHOS genes appeared in every group. Male epsilon-2 "
            "had the broadest overlap in the other three pathways: 67 of 86 nuclear "
            "structural OXPHOS genes, 130 of 155 mitochondrial-translation genes, and "
            "17 of 19 inner-membrane genes. Female epsilon-3 homozygous had narrower "
            "overlap in mitochondrial translation and inner-membrane organization."
        ),
        "boundary": (
            "This heatmap collapses across fine cell types and records presence, not "
            "direction, recurrence, effect size, or statistical enrichment. Groups "
            "with more overall DEGs will tend to overlap more pathway genes. Formal "
            "over-representation analysis instead uses the detectable-gene background "
            "within each comparison and controls the false-discovery rate."
        ),
    },
    12: {
        "goal": "Introduce the key-driver-analysis section.",
        "walkthrough": (
            "Part 3 follows mitochondrial DEGs from one fine-cell contrast into one "
            "network query, identifies significant returned key drivers, and then "
            "aggregates repeated fine-cell evidence within sex/APOE by broad-cell "
            "categories using returned-only ACAT."
        ),
        "boundary": (
            "KDA nominates network-associated candidate regulators. It does not prove "
            "that a returned gene causally controls the mitochondrial pathway, and it "
            "does not pool sex/APOE groups."
        ),
    },
    13: {
        "goal": "Define the category unit and the fine-cell-to-broad aggregation.",
        "walkthrough": (
            "Two sexes crossed with three APOE groups create six sex/APOE groups. "
            "Crossing each group with seven frozen broad cell types creates 42 "
            "possible categories; M_e33 by excitatory neurons is one example. "
            "Contrasts outnumber categories because several fine cell types can map "
            "to the same broad cell type. When the same driver returns from multiple "
            "fine-cell calls in one category, the returned within-call adjusted P "
            "values are combined by equal-weight ACAT into one gene-by-category score."
        ),
        "boundary": (
            "Forty-two is the structural design space, not 42 observed negative or "
            "positive results. A category may lack an eligible call or a returned "
            "non-mitochondrial driver. The ACAT is returned-only: a call in which the "
            "gene was not returned does not contribute P equals one."
        ),
    },
    15: {
        "goal": "Summarize ROSMAP as the primary discovery analysis before the detailed funnel.",
        "walkthrough": (
            "ROSMAP starts with 324 planned fine-cell contrasts. Those contrasts "
            "produce 194 executable KDA calls and 381 non-mitochondrial "
            "gene-by-category combinations, representing 228 distinct genes across "
            "29 populated categories. Each contrast contributes its mitochondrial "
            "DEG query, and returned fine-cell evidence is then aggregated within "
            "the matching sex/APOE-by-broad-cell category."
        ),
        "boundary": (
            "Planned contrasts, executable calls, and gene-by-category combinations "
            "are different units. The category results use returned-only ACAT, and "
            "the counts are descriptive rather than independent replication counts."
        ),
    },
    27: {
        "goal": "Summarize SEA-AD as supplemental human validation before the detailed funnel.",
        "walkthrough": (
            "SEA-AD starts with 774 planned supertype-level contrasts. Only 22 meet "
            "the source-validity and three-gene query requirements for KDA. These "
            "calls return 44 non-mitochondrial gene-by-category combinations, "
            "representing 43 distinct genes across five populated categories. The "
            "analysis uses SEA-AD-specific networks rather than reusing ROSMAP "
            "networks."
        ),
        "boundary": (
            "Coverage is sparse and unbalanced: 20 of the 22 calls are in the male "
            "epsilon-3 homozygous group. An unavailable category is not a negative "
            "validation result, and cohort differences in networks, phenotype, and "
            "query coverage limit direct one-to-one comparison."
        ),
    },
    39: {
        "goal": "Introduce the biological interpretation section.",
        "walkthrough": (
            "The next sections translate the DEG, pathway, KDA, and sensitivity "
            "results into 17 testable biological findings. They begin with the two "
            "cross-cohort OXPHOS patterns, then examine additional sex/APOE programs, "
            "candidate key drivers, cross-cell recurrence, and important limits on "
            "validation and interpretation."
        ),
        "boundary": (
            "These are evidence syntheses, not causal conclusions. SEA-AD support is "
            "graded according to matched coverage and may be program-level rather "
            "than exact-gene replication."
        ),
    },
}

def _slide_number_after_insertions(slide_number: int) -> int:
    """Map the original order through insertions and the two preview deletions."""
    after_overlap = slide_number + 1 if slide_number >= 8 else slide_number
    after_mitocarta = after_overlap + 1 if after_overlap >= 6 else after_overlap
    after_occurrence = after_mitocarta + 1 if after_mitocarta >= 11 else after_mitocarta
    return after_occurrence - 2 if after_occurrence >= 15 else after_occurrence


FULL_NOTE_OVERRIDES = {
    _slide_number_after_insertions(slide_number): fields
    for slide_number, fields in _PRE_OVERLAP_INSERT_NOTE_OVERRIDES.items()
}
FULL_NOTE_OVERRIDES[6] = {
    "goal": "Define the three MitoCarta pathway levels used in the analysis.",
    "walkthrough": (
        "MitoCarta organizes mitochondrial genes into a nested hierarchy. Level 1 "
        "contains seven broad mitochondrial systems. Level 2 contains 39 pathways "
        "within those systems. Level 3 adds 103 more detailed subpathways. For "
        "example, oxidative phosphorylation is a Level 1 system, Complex I is a "
        "Level 2 pathway within it, and Complex I subunits form a Level 3 pathway. "
        "Levels 1 and 2 therefore contain 46 pathways, while the complete hierarchy "
        "contains 149."
    ),
    "boundary": (
        "The levels describe biological specificity, not statistical strength. "
        "Because the hierarchy is nested, broad and detailed pathways can share "
        "genes and can produce related enrichment results. Counts come from the "
        "Phase 11 MitoCarta pathway manifest in "
        "results/minerva_production/11_pathway_deg_fine."
    ),
}
FULL_NOTE_OVERRIDES[9] = {
    "goal": (
        "Explain the overlap formula and its worked example."
    ),
    "walkthrough": (
        "This percentage summarizes one pathway within one sex/APOE group. The "
        "numerator is the number of unique pathway genes that were significant "
        "DEGs in at least one fine-cell comparison in that group. The denominator "
        "is the total number of genes in the pathway. Multiplying by 100 converts "
        "the ratio to a percentage. In the male epsilon-2 mitochondrial-translation "
        "example, 130 of the 155 pathway genes appeared as DEGs. Therefore, 130 "
        "divided by 155 times 100 equals 84 percent."
    ),
    "boundary": (
        "Each gene counts once, regardless of how many fine cell types contain it. "
        "The percentage does not show the percentage of fine cell types, the "
        "direction of change, recurrence across cell types, or pathway enrichment."
    ),
}
FULL_NOTE_OVERRIDES[11] = {
    "goal": (
        "Define an occurrence and show how the upregulated OXPHOS occurrence "
        "percentage is calculated."
    ),
    "walkthrough": (
        "Begin with the counting unit highlighted on the slide. One occurrence means "
        "that one pathway gene is a significant DEG in one fine-cell comparison. If "
        "the same gene is significant in another fine cell type, it contributes "
        "another occurrence. The calculation is performed separately for each "
        "sex/APOE group and each OXPHOS gene set. Divide the upregulated occurrences "
        "by all upregulated plus downregulated occurrences, then multiply by 100. In "
        "the male epsilon-3 homozygous mtDNA-encoded OXPHOS example, 70 occurrences "
        "were upregulated and 11 were downregulated. Seventy divided by 81 equals 86 "
        "percent upregulated. A value of 50 percent means the two directions occur "
        "equally often. Values above 50 percent favor upregulation, while values below "
        "50 percent favor downregulation."
    ),
    "boundary": (
        "This occurrence-based summary gives more weight to genes that recur across "
        "fine-cell comparisons. It is not a fold change, the percentage of unique "
        "genes, cells, donors, or fine cell types, an enrichment result, or a measure "
        "of OXPHOS activity. Repeated occurrences are not independent biological "
        "replications."
    ),
}
FULL_NOTE_OVERRIDES[35] = {
    "goal": (
        "Define an arm and show the numerical impact of raising the minimum "
        "donor requirement from three to five in both cohorts."
    ),
    "walkthrough": (
        "An arm is one disease-status group within a comparison. In ROSMAP, the "
        "two arms are AD and NCI. In SEA-AD, they are dementia and no dementia. "
        "A contrast is eligible only when each arm meets the stated donor minimum. "
        "Raising that minimum from three to five reduces ROSMAP from 42 to 40 "
        "eligible contrasts and from three to two KDA runs. Its returned driver "
        "rows fall from 39 to 13, and its unique non-mitochondrial drivers fall "
        "from 33 to 13. SEA-AD falls from 28 to 20 eligible contrasts, but its five "
        "KDA runs, 24 returned rows, and 18 unique non-mitochondrial drivers remain "
        "unchanged."
    ),
    "boundary": (
        "The threshold test changes only the donor eligibility gate. It does not "
        "change the retained contrast models, DEG queries, networks, or KDA "
        "settings. A contrast with fewer than five donors in either arm becomes "
        "unavailable under the stricter threshold; that exclusion is not a "
        "negative KDA result. Source: Phase 22 and VH14 run manifests and returns; "
        "donor-per-arm 3-versus-5 sensitivity assessment dated 2026-09-11."
    ),
}
FULL_NOTE_OVERRIDES[37] = {
    "goal": (
        "Define the query-size threshold and show how increasing it changes KDA "
        "availability and returned drivers."
    ),
    "walkthrough": (
        "The threshold is the minimum number of effective mitochondrial query "
        "genes remaining after network mapping. The donor minimum stays fixed at "
        "three in each disease-status group, so the source-estimable contrast "
        "counts remain 42 for ROSMAP and 28 for SEA-AD. One query is used for each "
        "contrast, which is why the query-passing contrast count equals the KDA-run "
        "count. In ROSMAP, increasing the threshold from three to ten genes reduces "
        "the analysis from three runs and 39 significant rows to one run and 26 "
        "rows. Thresholds of 20 and 30 make no further change. SEA-AD remains "
        "unchanged at five genes, falls to three runs and eight rows at ten or "
        "twenty genes, and retains two runs and seven rows at thirty genes."
    ),
    "boundary": (
        "This sensitivity analysis filters existing calls by mapped query size. It "
        "does not refit DEG models or rerun KDA for retained calls. Significant rows "
        "are raw KDA returns, while the final column excludes MT-* genes and "
        "deduplicates drivers within each cohort. Source: validated Phase 22 and "
        "VH14 run manifests and significant-return tables dated 2026-09-11."
    ),
}
FULL_NOTE_OVERRIDES[38] = {
    "goal": "Identify the seven KDA calls that create the query-threshold pattern.",
    "walkthrough": (
        "Read the ROSMAP panel first. Its three executed queries contain 3, 8, and "
        "78 mapped genes. A minimum of five removes the OPC female epsilon-4 call. "
        "A minimum of ten also removes the astrocyte female epsilon-4 call, leaving "
        "only the 78-gene vasculature male epsilon-2 call. That remaining call has "
        "low donor support, so raising the query floor makes the ROSMAP result more "
        "dependent on it. In SEA-AD, the five query sizes are 5, 9, 21, 43, and 45 "
        "genes. A minimum of five changes nothing. A minimum of ten removes the "
        "microglia male epsilon-3 homozygous and astrocyte female epsilon-4 calls, "
        "reducing the output from 24 to 8 rows and from 18 to 3 unique non-MT "
        "drivers. A minimum of thirty also removes the 21-gene oligodendrocyte call, "
        "but its only returned gene is MT-*, so the non-MT driver count remains three."
    ),
    "boundary": (
        "Query size means the number of effective mitochondrial genes after network "
        "mapping, not the number of donors, cells, or genes in a pathway. This test "
        "filters existing calls and does not rerun KDA. Returned MT-* genes explain "
        "changes in raw row counts but are not eligible non-mitochondrial key "
        "drivers. Source: validated Phase 22 and VH14 run manifests and "
        "significant-return tables dated 2026-09-11."
    ),
}
FULL_NOTE_OVERRIDES[40] = {
    "goal": "Introduce Part 5, the biological findings and discussion.",
    "walkthrough": (
        "Part 5 translates the DEG, pathway, KDA, and sensitivity results into 17 "
        "testable biological findings. It begins with two cross-cohort OXPHOS "
        "patterns, then examines additional sex/APOE-associated patterns, candidate "
        "key drivers, cross-cell recurrence, and the limits of validation and "
        "interpretation."
    ),
    "boundary": (
        "These findings synthesize transcriptomic and network evidence. They do not "
        "establish causality or mitochondrial function. SEA-AD support is graded "
        "according to matched coverage and may support a broader pathway pattern "
        "without reproducing the exact driver gene."
    ),
}

NOTE_PATTERN = re.compile(
    r"^Teaching goal:\s*(?P<goal>.*?)\n+"
    r"Walk through:\s*(?P<walkthrough>.*?)\n+"
    r"Scientific boundary:\s*(?P<boundary>.*?)\n+"
    r"Transition:\s*(?P<transition>.*)$",
    flags=re.DOTALL,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--output", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--audit-root", type=Path, default=AUDIT_ROOT)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def slide_title(slide) -> str:
    for shape in slide.shapes:
        if getattr(shape, "has_text_frame", False) and shape.text.strip():
            return " ".join(shape.text.split())
    return ""


def visual_fingerprint(slide) -> tuple[tuple[object, ...], ...]:
    """Capture all slide objects except speaker notes."""
    return tuple(
        (
            int(shape.shape_type),
            shape.name,
            int(shape.left),
            int(shape.top),
            int(shape.width),
            int(shape.height),
            shape.text if getattr(shape, "has_text_frame", False) else "",
        )
        for shape in slide.shapes
    )


def read_structured_notes(slide, slide_number: int) -> dict[str, str]:
    frame = slide.notes_slide.notes_text_frame
    text = frame.text.strip() if frame is not None else ""
    match = NOTE_PATTERN.match(text)
    if match is None:
        raise RuntimeError(
            f"Slide {slide_number} does not contain the expected structured notes"
        )
    return {key: value.strip() for key, value in match.groupdict().items()}


def write_notes(slide, fields: dict[str, str]) -> None:
    frame = slide.notes_slide.notes_text_frame
    if frame is None:
        raise RuntimeError("Notes placeholder is unavailable")
    frame.text = (
        f"Teaching goal: {fields['goal']}\n\n"
        f"Walk through: {fields['walkthrough']}\n\n"
        f"Scientific boundary: {fields['boundary']}\n\n"
        f"Transition: {fields['transition']}"
    )


def validate_deck(prs: Presentation) -> None:
    observed = tuple(slide_title(slide) for slide in prs.slides)
    if observed != EXPECTED_TITLES:
        mismatches = [
            f"slide {index}: expected {expected!r}, found {actual!r}"
            for index, (expected, actual) in enumerate(
                zip(EXPECTED_TITLES, observed), start=1
            )
            if expected != actual
        ]
        if len(observed) != len(EXPECTED_TITLES):
            mismatches.append(
                f"expected {len(EXPECTED_TITLES)} slides, found {len(observed)}"
            )
        raise RuntimeError("Unexpected reviewed deck structure: " + "; ".join(mismatches))


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    audit_root = args.audit_root.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)

    input_hash = sha256(input_path)
    prs = Presentation(input_path)
    validate_deck(prs)
    before = tuple(visual_fingerprint(slide) for slide in prs.slides)

    for slide_number, (slide, transition) in enumerate(
        zip(prs.slides, TRANSITIONS), start=1
    ):
        fields = read_structured_notes(slide, slide_number)
        fields.update(FULL_NOTE_OVERRIDES.get(slide_number, {}))
        fields["transition"] = transition
        write_notes(slide, fields)

    if tuple(visual_fingerprint(slide) for slide in prs.slides) != before:
        raise RuntimeError("A slide changed while synchronizing speaker notes")

    audit_root.mkdir(parents=True, exist_ok=True)
    backup_dir = audit_root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"input_deck_{input_hash[:12]}.pptx"
    if not backup_path.exists():
        shutil.copy2(input_path, backup_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        prefix=output_path.stem + ".", suffix=".pptx", dir=output_path.parent
    )
    os.close(handle)
    temp_path = Path(temp_name)
    try:
        prs.save(temp_path)
        reopened = Presentation(temp_path)
        validate_deck(reopened)
        if tuple(visual_fingerprint(slide) for slide in reopened.slides) != before:
            raise RuntimeError("Saved deck did not preserve all slide content")
        for slide_number, (slide, transition) in enumerate(
            zip(reopened.slides, TRANSITIONS), start=1
        ):
            fields = read_structured_notes(slide, slide_number)
            if fields["transition"] != transition:
                raise RuntimeError(
                    f"Slide {slide_number} transition failed round-trip validation"
                )
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    print(f"Updated speaker notes: {output_path}")
    print(f"Slides validated: {len(EXPECTED_TITLES)}")
    print(f"Backup: {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
