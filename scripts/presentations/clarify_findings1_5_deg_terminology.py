#!/usr/bin/env python3
"""Remove KDA-specific and undefined terminology from Findings 1–5."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from lxml import etree


A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"a": A_NS}


SLIDE_NODE_REPLACEMENTS: dict[int, dict[int, tuple[str, str]]] = {
    49: {
        5: ("For ", "Within "),
        6: ("e", "excitatory"),
        7: ("xcitatory-neuron only", " neurons"),
        9: ("e", "f"),
        10: ("ligible fine-cell DEG queries", "ine-cell DEG lists included"),
        15: ("For all eligible F_e33 KDA calls", "All included female ε3/ε3 DEG lists"),
    },
    50: {
        1: (
            "Only one matched female ε3/ε3 excitatory KDA call was evaluable, so support is strong in direction but limited in coverage.",
            "Only one SEA-AD fine-cell DEG list contributed to the matched female ε3/ε3 excitatory-neuron comparison, so coverage is limited.",
        ),
        3: (
            "SEA query genes include nine shared core MT genes",
            "SEA-AD MitoCarta MT DEGs also found in ROSMAP",
        ),
        6: ("BH = 0.005", "Adjusted P = 0.005"),
        7: ("cross-cohort overlap after correction", "shared-gene overlap between cohorts"),
        9: ("Nine shared genes", "Nine shared core MT genes"),
        19: (
            "Every shared gene is upregulated in both datasets.",
            "All nine core MT genes are upregulated in both cohorts.",
        ),
    },
    52: {
        5: (
            "Supports sex-aware key-driver analysis.",
            "Supports analyzing AD networks separately by sex.",
        ),
    },
    53: {
        2: (
            "A mitochondrial pathway finding based on DEGs, not an identified upstream key driver.",
            "A mitochondrial DEG finding based on the directions of two defined OXPHOS gene sets.",
        ),
        12: (
            "SEA-AD supports the inhibitory-neuron DEG pattern without matching the same genes returned from ROSMAP KDA calls.",
            "SEA-AD supports the inhibitory-neuron pattern through shared DEGs with matching AD directions.",
        ),
    },
    54: {
        4: ("Inhibitory support", "Inhibitory neurons"),
        13: (
            "Finding 2 synthesis; ROSMAP discovery with supplemental SEA-AD gene-set support.",
            "ROSMAP provides the primary evidence. SEA-AD adds support from matched inhibitory-neuron DEGs.",
        ),
    },
    55: {
        1: (
            "Across 31 eligible fine-cell DEG queries; occurrences repeat genes across KDA calls.",
            "Across 31 included fine-cell DEG lists. The same gene can recur in different comparisons.",
        ),
    },
    56: {
        0: (
            "SEA-AD supports the matched male ε3/ε3 inhibitory-neuron gene-set pattern",
            "SEA-AD supports the matched male ε3/ε3 inhibitory-neuron DEG pattern",
        ),
        1: (
            "Eight eligible SEA-AD fine-cell DEG queries contributed. Support comes from shared MitoCarta MT DEGs and matching AD directions.",
            "Eight SEA-AD fine-cell DEG lists contributed. Support comes from shared MitoCarta MT DEGs with the same AD direction.",
        ),
        6: ("BH = 0.0417", "Adjusted P = 0.0417"),
        7: ("cross-cohort overlap after correction", "shared-gene overlap between cohorts"),
        12: ("Nuclear support systems", "Nuclear-encoded MT genes"),
        14: (
            "OXPHOS, import, ribosome, and maintenance genes are AD-down in both cohorts",
            "Genes for OXPHOS, protein import, mitochondrial ribosomes, and DNA/RNA maintenance are AD-down in both cohorts",
        ),
        15: (
            "Identity-resolved sensitivity: 21 shared genes, BH = 0.0486.",
            "Sensitivity check excluding genes with uncertain mitochondrial identity: 21 shared, adjusted P = 0.0486.",
        ),
    },
    57: {
        0: (
            "Which genes carry the matched inhibitory-neuron signal?",
            "Which genes account for the matched inhibitory-neuron pattern?",
        ),
        1: (
            "The agreement spans respiratory subunits, transport, import, mitochondrial ribosomes, and maintenance.",
            "Shared genes include OXPHOS subunits and genes for protein import, mitochondrial ribosomes, and DNA/RNA maintenance.",
        ),
        21: ("Other concordant genes", "Other genes with the same direction"),
        23: ("3 discordant genes", "3 genes with opposite directions"),
    },
    58: {
        6: ("Support systems also fall", "Other mitochondrial processes also decrease"),
        7: (
            "Import, mitochondrial-ribosome, transport, and maintenance genes are down in both cohorts.",
            "Genes for protein import, mitochondrial ribosomes, metabolite transport, and DNA/RNA maintenance are down in both cohorts.",
        ),
    },
    59: {
        0: (
            "Prior research supports the ingredients—but not this exact mismatch",
            "Prior research supports the biological context, but not this exact pattern",
        ),
        1: (
            "Known mitonuclear biology and cell-resolved AD studies make the finding plausible without independently duplicating it.",
            "Two-genome OXPHOS biology and cell-resolved AD studies make the finding plausible without independently reproducing it.",
        ),
        2: ("Mitonuclear biology", "Two-genome OXPHOS biology"),
        20: (
            "Novelty assessment: high—mitonuclear imbalance is known, but this cross-cohort male ε3/ε3 inhibitory-neuron pattern was not identified previously.",
            "Novelty assessment: high. Opposite OXPHOS directions are biologically plausible, but this cross-cohort male ε3/ε3 inhibitory-neuron pattern was not identified previously.",
        ),
    },
    60: {
        2: ("nucler", "nuclear"),
    },
    61: {
        1: (
            "The two genomes move in the same direction at the RNA level, especially in fine excitatory-neuron results.",
            "The two OXPHOS gene sets move in the same direction at the RNA level, especially in fine excitatory-neuron results.",
        ),
        5: ("AD versus NCI", "AD versus no cognitive impairment"),
        8: ("occurrances", "occurrences"),
    },
    62: {
        1: (
            "Occurrences repeat a gene when it appears in another eligible fine-cell query.",
            "A gene contributes another occurrence when it is a DEG in another included fine-cell comparison.",
        ),
        10: (
            "127 AD-up and 1 AD-down occurrence across eligible KDA calls",
            "127 AD-up and 1 AD-down occurrence across included fine-cell comparisons",
        ),
        13: (
            "239 AD-up and 4 AD-down occurrences across eligible KDA calls",
            "239 AD-up and 4 AD-down occurrences across included fine-cell comparisons",
        ),
    },
    63: {
        2: ("PHASE 11", "FINE-CELL ROSMAP"),
        4: (
            "Nine of 12 fine types enriched core MT upregulation and eight of 12 enriched nuclear-encoded OXPHOS upregulation.",
            "Significant enrichment of upregulated genes appeared in 9 of 12 fine cell types for core MT genes and 8 of 12 for nuclear-encoded OXPHOS genes.",
        ),
        9: ("Not evaluable", "No matched DEG result"),
        10: (
            "No matching female ε2 category was active. Missing coverage adds no evidence for or against the finding.",
            "No matched female ε2 fine-cell DEG result was available. This adds no evidence for or against the finding.",
        ),
        11: (
            "The coordinated two-genome claim rests mainly on fine-cell ROSMAP evidence.",
            "The coordinated two-gene-set pattern rests mainly on fine-cell ROSMAP evidence.",
        ),
    },
    69: {
        4: (
            "Excitatory nuclear-encoded OXPHOS NES was +0.70 with local BH 0.991.",
            "Excitatory nuclear-encoded OXPHOS: normalized enrichment score (NES) = +0.70, adjusted P = 0.991.",
        ),
        7: (
            "Excitatory nuclear-encoded OXPHOS NES was +2.01 with local BH 5.62 × 10⁻⁵.",
            "Excitatory nuclear-encoded OXPHOS: normalized enrichment score (NES) = +2.01, adjusted P = 5.62 × 10⁻⁵.",
        ),
        8: ("SEA-AD FINE-CELL KDA", "SEA-AD FINE-CELL DEG CHECK"),
        9: ("Only one small astrocyte query", "One small astrocyte DEG list"),
        10: (
            "Two genes overlapped and the corrected overlap test was not significant, BH 0.819.",
            "Only two DEGs were shared with ROSMAP. Adjusted overlap P = 0.819.",
        ),
    },
    73: {
        4: ("Both genomes down", "Both gene sets down"),
        5: ("Large queries", "Large DEG sets"),
    },
    74: {
        0: (
            "ROSMAP: male ε2 has the broadest downward OXPHOS burden",
            "ROSMAP: male ε2 has the most downward OXPHOS DEG occurrences",
        ),
    },
    75: {
        1: (
            "The DEG-set size matters when comparing how many genes are returned from KDA calls.",
            "Larger DEG sets help explain why male ε2 contributes many DEG occurrences.",
        ),
        4: (
            "The median eligible query was more than five times the overall median.",
            "The median male ε2 DEG set was more than five times the overall median.",
        ),
        5: (
            "ALL ELIGIBLE FINE-CELL COMPARISONS",
            "ALL INCLUDED FINE-CELL COMPARISONS",
        ),
        7: (
            "The overall median shows how unusual the male ε2 query size was.",
            "The overall median shows how unusual the male ε2 DEG-set size was.",
        ),
        9: ("Not evaluable", "No matched DEG result"),
        10: (
            "No matching male ε2 category was active, so SEA-AD adds no evidence in either direction.",
            "No matched male ε2 fine-cell DEG result was available, so SEA-AD adds no evidence in either direction.",
        ),
        11: (
            "More DEGs provide more opportunities for a gene to be returned from a KDA call. This does not change the DEG direction counts on the preceding slide.",
            "Larger DEG sets can produce more DEG occurrences across fine-cell comparisons. This does not change the direction percentages on the preceding slide.",
        ),
    },
}


NOTES_REPLACEMENTS: dict[int, dict[str, str]] = {
    49: {
        "Walk through: F_e33 denotes the female APOE epsilon-3 homozygous group. Across eligible fine-cell DEG input queries, core MT genes contribute 217 occurrences, and all 217 occurrences are upregulated in AD. Nuclear-encoded OXPHOS genes appear 89 times, with 76 upregulated and 13 downregulated, so 85 percent are upregulated. Within excitatory neurons, 14 eligible fine-cell DEG queries contain 123 core MT gene occurrences, all upregulated. One occurrence means that one pathway gene is a DEG in one fine-cell comparison. The same gene can therefore contribute multiple occurrences across fine cell types. These displayed numbers summarize DEG occurrences and their direction across eligible queries.":
            "Walk through: F_e33 denotes the female APOE epsilon-3 homozygous group. Across the included fine-cell DEG lists, core MT genes contribute 217 occurrences, and all 217 are upregulated in AD. Nuclear-encoded OXPHOS genes contribute 89 occurrences: 76 upregulated and 13 downregulated, so 85 percent are upregulated. Within excitatory neurons, 14 included fine-cell DEG lists contain 123 core MT gene occurrences, all upregulated. One occurrence means that one gene is a DEG in one fine-cell comparison, so the same gene can contribute multiple occurrences across fine cell types. These counts summarize the fine-cell DEG lists used for the mitochondrial analysis.",
        "Scientific boundary: The occurrence counts do not represent unique genes, expression magnitude, independent donors, or genes returned from KDA calls. The KDA input query is the mitochondrial DEG list supplied to that call.":
            "Scientific boundary: The occurrence counts do not represent unique genes, expression magnitude, independent donors, or replication. They summarize repeated DEG observations across fine-cell comparisons.",
    },
    50: {
        "Walk through: Only one matched female epsilon-3 homozygous excitatory-neuron KDA call was evaluable in SEA-AD, so the coverage is narrow. Its effective query contains 10 genes. Nine are the same core MT genes found in ROSMAP, and all nine are upregulated in the disease group in both cohorts. The analysis observed nine shared genes compared with 3.83 expected under the category-specific background model. The overlap remains significant after correction, with a Benjamini-Hochberg-adjusted P value of 0.005.":
            "Walk through: Only one SEA-AD fine-cell DEG list contributed to the matched female epsilon-3 homozygous excitatory-neuron comparison, so the coverage is narrow. The list contains 10 MitoCarta MT DEGs. Nine are the same core MT genes found in ROSMAP, and all nine are upregulated in AD in both cohorts. The analysis observed nine shared genes compared with 3.83 expected based on genes detectable in the matched comparison. The shared-gene overlap remained significant after multiple-testing correction, with an adjusted P value of 0.005.",
        "Scientific boundary: This slide supports the core MT component of Finding 1. It does not establish broad replication across excitatory-neuron subtypes or cross-cohort replication of the secondary nuclear-encoded OXPHOS increase. It also does not require SEA-AD to return the same upstream gene from a KDA call.":
            "Scientific boundary: This slide supports the core MT component of Finding 1. It does not establish broad replication across excitatory-neuron subtypes or cross-cohort replication of the secondary nuclear-encoded OXPHOS increase.",
    },
    52: {
        "Transition: Proceed to Finding 2, the male epsilon-3 homozygous mitonuclear mismatch.":
            "Transition: Proceed to Finding 2, the male epsilon-3 homozygous pattern with opposite OXPHOS directions.",
    },
    53: {
        "Scientific boundary: This is a transcript-level pattern across mitochondrial gene sets. It does not identify a causal upstream driver, prove protein imbalance, or establish a male-by-APOE interaction.":
            "Scientific boundary: This is a transcript-level pattern across two mitochondrial gene sets. It does not prove protein imbalance, mitochondrial dysfunction, or a male-by-APOE interaction.",
    },
    54: {
        "Teaching goal: Explain the mitonuclear mismatch without statistical jargon.":
            "Teaching goal: Explain the opposite OXPHOS gene-expression directions without statistical jargon.",
    },
    55: {
        "Walk through: Across 31 eligible male epsilon-3 homozygous fine-cell DEG queries used to make KDA calls, core MT genes contributed 81 occurrences: 70 AD-up and 11 AD-down. Therefore, 86 percent were upregulated. Nuclear-encoded OXPHOS genes contributed 68 occurrences: 8 AD-up and 60 AD-down. Therefore, 88 percent were downregulated. An occurrence is one pathway gene identified as a DEG in one fine-cell comparison, so the same gene can contribute again in another fine cell type.":
            "Walk through: Across 31 included male epsilon-3 homozygous fine-cell DEG lists, core MT genes contributed 81 occurrences: 70 AD-up and 11 AD-down. Therefore, 86 percent were upregulated. Nuclear-encoded OXPHOS genes contributed 68 occurrences: 8 AD-up and 60 AD-down. Therefore, 88 percent were downregulated. An occurrence is one gene identified as a DEG in one fine-cell comparison, so the same gene can contribute again in another fine cell type.",
        "Scientific boundary: These are occurrences among the mitochondrial DEG input queries, not unique genes, independent donors, or genes returned from KDA calls. Opposite directions in gene expression do not demonstrate mismatched proteins or impaired respiration.":
            "Scientific boundary: These are repeated DEG occurrences, not counts of unique genes or independent donors. Opposite directions in gene expression do not demonstrate mismatched proteins or impaired respiration.",
    },
    56: {
        "Teaching goal: Explain the matched SEA-AD DEG support and what cross-cohort directional agreement means here.":
            "Teaching goal: Explain the matched SEA-AD DEG support and what the same AD direction across cohorts means here.",
        "Walk through: Eight eligible SEA-AD male epsilon-3 homozygous inhibitory-neuron fine-cell DEG queries contributed to this comparison. ROSMAP and SEA-AD shared 22 MitoCarta MT DEGs, and 19 of the 22 had the same AD direction. Nine core MT genes were upregulated in both cohorts. Nuclear-encoded OXPHOS, protein-import, mitochondrial-ribosome, and maintenance genes were downregulated in both. The overlap was 22 genes compared with 15.17 expected and remained significant after correction, with a Benjamini-Hochberg adjusted P value of 0.0417. Excluding unresolved mitochondrial identity-conflict genes left 21 shared genes and a similar adjusted P value of 0.0486. The support therefore comes from shared DEGs and their directions across cohorts.":
            "Walk through: Eight SEA-AD male epsilon-3 homozygous inhibitory-neuron fine-cell DEG lists contributed to this comparison. ROSMAP and SEA-AD shared 22 MitoCarta MT DEGs, and 19 of the 22 had the same AD direction. Nine core MT genes were upregulated in both cohorts. Genes for nuclear-encoded OXPHOS, mitochondrial protein import, mitochondrial ribosomes, metabolite transport, and mitochondrial DNA or RNA maintenance were downregulated in both. The overlap was 22 genes compared with 15.17 expected and remained significant after multiple-testing correction, with an adjusted P value of 0.0417. Excluding genes whose mitochondrial identity was uncertain left 21 shared genes and a similar adjusted P value of 0.0486. The support therefore comes from shared DEGs and their directions across cohorts.",
    },
    57: {
        "Teaching goal: Name the concordant and discordant genes in the matched inhibitory-neuron comparison.":
            "Teaching goal: Name the genes with the same or opposite AD directions in the matched inhibitory-neuron comparison.",
        "Scientific boundary: These directions describe shared mitochondrial-query DEGs rather than genes returned from KDA calls. Directional agreement does not establish matched protein abundance, respiratory-complex assembly, or mitochondrial function.":
            "Scientific boundary: These are shared MitoCarta MT DEGs. Matching AD directions do not establish matched protein abundance, respiratory-complex assembly, or mitochondrial function.",
    },
    58: {
        "Transition: Place the finding in prior mitonuclear and cell-resolved Alzheimer’s research.":
            "Transition: Place the finding in prior two-genome OXPHOS and cell-resolved Alzheimer’s research.",
    },
    59: {
        "Walk through: General mitonuclear biology establishes that OXPHOS requires coordinated mitochondrial-encoded and nuclear-encoded parts, but it does not show a protein imbalance in these samples. Guo and colleagues support analyzing Alzheimer’s molecular networks separately by sex, but they do not test this exact male epsilon-3 homozygous mismatch. Mathys and colleagues support strong cell-resolved Alzheimer’s responses, but their study also uses ROSMAP and therefore does not provide independent replication. The novelty assessment is high because the biological concept is established while this cross-cohort male epsilon-3 homozygous inhibitory-neuron pattern was not identified in the reviewed literature.":
            "Walk through: Basic OXPHOS biology establishes that respiratory complexes require coordinated core MT and nuclear-encoded OXPHOS proteins, but it does not show a protein imbalance in these samples. Guo and colleagues support analyzing Alzheimer’s molecular networks separately by sex, but they do not test this exact male epsilon-3 homozygous pattern. Mathys and colleagues support strong cell-resolved Alzheimer’s responses, but their study also uses ROSMAP and therefore does not provide independent replication. The novelty assessment is high because the biological concept is established while this cross-cohort male epsilon-3 homozygous inhibitory-neuron pattern was not identified in the reviewed literature.",
    },
    61: {
        "Walk through: Core MT genes are the 13 protein-coding mitochondrial-DNA genes that encode structural OXPHOS subunits. Nuclear-encoded OXPHOS genes are the 86 nuclear genes that encode the remaining structural subunits used in this analysis. Across eligible female APOE ε2 fine-cell comparisons, 127 of 128 core MT gene occurrences and 239 of 243 nuclear-encoded OXPHOS gene occurrences were upregulated in AD. The result is therefore a coordinated transcript-level pattern across both gene sets.":
            "Walk through: Core MT genes are the 13 protein-coding mitochondrial-DNA genes that encode structural OXPHOS subunits. Nuclear-encoded OXPHOS genes are the 86 nuclear genes that encode the remaining structural subunits used in this analysis. Across included female APOE ε2 fine-cell comparisons, 127 of 128 core MT gene occurrences and 239 of 243 nuclear-encoded OXPHOS gene occurrences were upregulated in AD. The result is therefore a coordinated RNA-level pattern across both gene sets.",
        "Scientific boundary: An occurrence is one pathway gene identified as a DEG in one eligible fine-cell comparison, so the same gene may appear more than once across cell types. These counts do not measure unique genes, protein assembly, respiration, or ATP production.":
            "Scientific boundary: An occurrence is one gene identified as a DEG in one included fine-cell comparison, so the same gene may appear more than once across cell types. These counts do not measure unique genes, protein assembly, respiration, or ATP production.",
        "Transition: Show the complete ROSMAP occurrence and enrichment counts.":
            "Transition: Show the complete ROSMAP DEG-occurrence counts.",
    },
    62: {
        "Walk through: Across eligible female APOE ε2 fine-cell comparisons used for KDA, core MT genes contribute 128 DEG occurrences: 127 AD-up and one AD-down, so 99 percent are upregulated. Nuclear-encoded OXPHOS genes contribute 243 DEG occurrences: 239 AD-up and four AD-down, so 98 percent are upregulated. One occurrence means that one gene is a DEG in one eligible fine-cell comparison; the same gene can contribute another occurrence in another comparison.":
            "Walk through: This slide quantifies the female APOE epsilon-2 pattern. Across the included fine-cell comparisons, core MT genes contribute 128 DEG occurrences: 127 AD-up and one AD-down, so 99 percent are upregulated. Nuclear-encoded OXPHOS genes contribute 243 DEG occurrences: 239 AD-up and four AD-down, so 98 percent are upregulated. Both OXPHOS gene sets therefore show an almost uniform increase in AD.",
        "Scientific boundary: The numbers 128 and 243 are gene-by-comparison occurrences, not counts of unique genes, cells, donors, or genes returned from KDA calls. The percentages do not measure expression magnitude, OXPHOS protein abundance, respiration, or ATP production.":
            "Scientific boundary: The numbers 128 and 243 are gene-by-comparison occurrences, not counts of unique genes, cells, or donors. The percentages do not measure expression magnitude, OXPHOS protein abundance, respiration, or ATP production.",
    },
    63: {
        "Walk through: The project treats fine-cell results as primary and direct broad-cell results as sensitivity evidence. In the fine-cell analysis, nine of 12 excitatory fine cell types support core MT upregulation and eight of 12 support nuclear-encoded OXPHOS upregulation. In the direct broad-cell ROSMAP analysis, the nuclear-encoded OXPHOS increase remains strong, but the core MT component is not significant. SEA-AD has no active matched female APOE ε2 category, so it cannot test this finding.":
            "Walk through: The project treats fine-cell results as primary and direct broad-cell results as sensitivity evidence. In the fine-cell pathway analysis, nine of 12 excitatory fine cell types had significant enrichment of upregulated core MT genes and eight of 12 had significant enrichment of upregulated nuclear-encoded OXPHOS genes. In the direct broad-cell ROSMAP analysis, the nuclear-encoded OXPHOS increase remains strong, but the core MT component is not significant. SEA-AD has no matched female APOE ε2 fine-cell DEG result for this comparison.",
    },
    68: {
        "Walk through: Across eligible fine-cell comparisons, nuclear-encoded OXPHOS genes contribute 216 DEG occurrences: 206 AD-down and 10 AD-up. Thus 95 percent are downregulated. Core MT genes contribute 64 occurrences: 38 AD-down and 26 AD-up, or 59 percent downregulated. The nuclear-encoded component is both larger and much more consistently downward.":
            "Walk through: Across included fine-cell comparisons, nuclear-encoded OXPHOS genes contribute 216 DEG occurrences: 206 AD-down and 10 AD-up. Thus 95 percent are downregulated. Core MT genes contribute 64 occurrences: 38 AD-down and 26 AD-up, or 59 percent downregulated. The nuclear-encoded component is both larger and much more consistently downward.",
        "Scientific boundary: These are repeated gene-by-fine-cell DEG occurrences. They are not counts of unique genes, cells, donors, or genes returned from KDA calls, and they do not quantify the magnitude of expression change.":
            "Scientific boundary: These are repeated gene-by-fine-cell DEG occurrences. They are not counts of unique genes, cells, or donors, and they do not quantify the magnitude of expression change.",
    },
    69: {
        "Walk through: The fine-cell DEG result points strongly downward for nuclear-encoded OXPHOS genes. In direct broad-cell analysis, however, the ROSMAP excitatory-neuron score is weakly positive and not significant, while the SEA-AD excitatory-neuron score is significantly positive. The available SEA-AD fine-cell check is only one small astrocyte comparison and does not provide convincing support.":
            "Walk through: The fine-cell DEG result points strongly downward for nuclear-encoded OXPHOS genes. The normalized enrichment score, or NES, summarizes the direction and strength of a pathway result; a positive NES indicates higher pathway expression in AD. In direct broad-cell analysis, the ROSMAP excitatory-neuron NES is weakly positive and not significant, while the SEA-AD excitatory-neuron NES is significantly positive. The available SEA-AD fine-cell check is only one small astrocyte DEG list and does not provide convincing support.",
    },
    72: {
        "Walk through: Unlike Finding 4, both defined OXPHOS gene sets move downward in male APOE ε2 fine-cell comparisons. Core MT genes are predominantly AD-down, and nuclear-encoded OXPHOS genes are also predominantly AD-down. The next slides quantify the repeated DEG occurrences and show why the unusually large MitoCarta MT DEG sets matter for interpreting later KDA output.":
            "Walk through: Unlike Finding 4, both defined OXPHOS gene sets move downward in male APOE ε2 fine-cell comparisons. Core MT genes are predominantly AD-down, and nuclear-encoded OXPHOS genes are also predominantly AD-down. The next slides quantify the repeated DEG occurrences and explain why unusually large MitoCarta MT DEG sets contribute many occurrences.",
    },
    74: {
        "Walk through: Across eligible fine-cell comparisons, core MT genes contribute 132 DEG occurrences: 119 AD-down and 13 AD-up, so 90 percent are downregulated. Nuclear-encoded OXPHOS genes contribute 467 occurrences: 404 AD-down and 63 AD-up, so 87 percent are downregulated. Together, 523 OXPHOS occurrences are AD-down.":
            "Walk through: Across included fine-cell comparisons, core MT genes contribute 132 DEG occurrences: 119 AD-down and 13 AD-up, so 90 percent are downregulated. Nuclear-encoded OXPHOS genes contribute 467 occurrences: 404 AD-down and 63 AD-up, so 87 percent are downregulated. Together, 523 OXPHOS occurrences are AD-down.",
        "Scientific boundary: The 523 value combines repeated gene-by-fine-cell occurrences from two defined gene sets. It is not a count of unique genes, donors, cells, or genes returned from KDA calls, and it does not measure expression magnitude or mitochondrial function.":
            "Scientific boundary: The 523 value combines repeated gene-by-fine-cell occurrences from two defined gene sets. It is not a count of unique genes, donors, or cells, and it does not measure expression magnitude or mitochondrial function.",
    },
    75: {
        "Walk through: For each fine-cell comparison, DEGs are restricted to MitoCarta MT genes and to genes available in the relevant network before making the KDA call. The median male APOE ε2 set contains 85 such DEGs, compared with 16.5 across all eligible fine-cell comparisons. More input DEGs create more opportunities for a gene to be returned from a KDA call.":
            "Walk through: Each included fine-cell comparison contributes one set of MitoCarta MT DEGs. The median male APOE ε2 set contains 85 DEGs, compared with 16.5 across all included fine-cell comparisons. Larger DEG sets can generate more DEG occurrences when results are summarized across fine cell types.",
        "Scientific boundary: This size difference affects comparisons of KDA output counts. It does not change the observed AD-up versus AD-down DEG occurrence counts on the preceding slide. SEA-AD has no matching active male APOE ε2 category here.":
            "Scientific boundary: This size difference helps explain the large occurrence count, but it does not change the proportion of upregulated versus downregulated occurrences. SEA-AD has no matched male APOE ε2 fine-cell DEG result here.",
        "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 5 and KDA query-size diagnostics.":
            "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 5 and DEG-set-size diagnostics.",
    },
}


def _update_part(xml: bytes, part: str) -> bytes:
    root = etree.fromstring(xml)
    nodes = root.xpath(".//a:t", namespaces=NS)

    if part.startswith("ppt/slides/slide"):
        slide_number = int(part.removeprefix("ppt/slides/slide").removesuffix(".xml"))
        for index, (old, new) in SLIDE_NODE_REPLACEMENTS.get(slide_number, {}).items():
            if index >= len(nodes) or nodes[index].text != old:
                actual = None if index >= len(nodes) else nodes[index].text
                raise RuntimeError(
                    f"Unexpected text in slide {slide_number}, node {index}: {actual!r}; expected {old!r}"
                )
            nodes[index].text = new
    else:
        slide_number = int(
            part.removeprefix("ppt/notesSlides/notesSlide").removesuffix(".xml")
        )
        by_text: dict[str, list[etree._Element]] = {}
        for node in nodes:
            by_text.setdefault(node.text or "", []).append(node)
        for old, new in NOTES_REPLACEMENTS.get(slide_number, {}).items():
            matches = by_text.get(old, [])
            if len(matches) != 1:
                raise RuntimeError(
                    f"Expected one notes match on slide {slide_number}, found {len(matches)}: {old!r}"
                )
            matches[0].text = new

    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=True,
    )


def revise(source: Path, destination: Path) -> None:
    changed_parts = {
        *(f"ppt/slides/slide{i}.xml" for i in SLIDE_NODE_REPLACEMENTS),
        *(f"ppt/notesSlides/notesSlide{i}.xml" for i in NOTES_REPLACEMENTS),
    }
    with zipfile.ZipFile(source, "r") as src, zipfile.ZipFile(destination, "w") as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename in changed_parts:
                data = _update_part(data, item.filename)
            dst.writestr(item, data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    revise(args.source, args.destination)


if __name__ == "__main__":
    main()
