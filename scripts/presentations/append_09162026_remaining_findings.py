#!/usr/bin/env python3
"""Append Findings 3 through 17 to the reviewed 2026-09-16 presentation.

Each finding follows the seven-slide teaching pattern established by Findings 1
and 2: divider, plain-language statement, ROSMAP evidence, evidence context,
biological meaning, limitations and next tests, and prior-research context.
The first 54 slides are treated as authoritative and their visuals are preserved.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Pt


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import update_phase11_seaad_simple_aggr_part2 as ui  # noqa: E402
from append_finding1_slides import (  # noqa: E402
    add_chip,
    add_content_title,
    add_notes,
    add_source,
    add_stat_card,
    set_shape_text,
)


DEFAULT_DECK = (
    ROOT
    / "docs"
    / "presentations"
    / "09162026"
    / "09162026_sex_apoe_kda_fine_broad.pptx"
)
AUDIT_ROOT = ROOT / "results" / "presentations" / "09162026_remaining_findings"
ANALYSIS_SOURCE = (
    "docs/analysis/kda_w_human_validation/"
    "rosmap_sex_apoe_broad_kda_analysis.md"
)
BASE_SLIDES = 54
SLIDES_PER_FINDING = 7
DIVIDER_TEMPLATE_INDEX = 39


def card(label: str, headline: str, body: str, tone: str = "blue") -> dict[str, str]:
    return {"label": label, "headline": headline, "body": body, "tone": tone}


def literature(
    citation: str,
    topic: str,
    supports: str,
    boundary: str,
    url: str = "",
) -> dict[str, str]:
    return {
        "citation": citation,
        "topic": topic,
        "supports": supports,
        "boundary": boundary,
        "url": url,
    }


FINDINGS: tuple[dict[str, Any], ...] = (
    {
        "number": 3,
        "title": "Female APOE ε2 cells show coordinated increases from both genomes",
        "kind": "Mitochondrial DEG-program finding",
        "novelty": "High",
        "divider_note": "Both mitochondrial and nuclear OXPHOS RNA mostly increased in female ε2 cells.",
        "plain_title": "Female ε2 cells raise both mitochondrial and nuclear OXPHOS RNA in AD",
        "plain_subtitle": "The two genomes move in the same direction at the RNA level, especially in fine excitatory-neuron results.",
        "tags": ("Female", "APOE ε2", "Fine cell types", "AD versus NCI"),
        "concepts": (
            card("Mitochondrial DNA", "127 of 128 up", "The mitochondrial genome supplies 13 core OXPHOS subunits.", "blue"),
            card("Nuclear DNA", "239 of 243 up", "The nuclear genome supplies most structural OXPHOS subunits.", "green"),
            card("Reading", "Coordinated RNA", "Both instruction sets rise together. Protein assembly and ATP remain unmeasured.", "gold"),
        ),
        "plain_bottom": "This is a coordinated transcriptional response, not evidence that mitochondria produce more energy.",
        "evidence_title": "ROSMAP: female ε2 OXPHOS occurrences are almost uniformly AD-up",
        "evidence_subtitle": "Occurrences repeat a gene when it appears in another eligible fine-cell query.",
        "metrics": (("128", "mtDNA-OXPHOS occurrences", "127 up, 1 down"), ("243", "nuclear-OXPHOS occurrences", "239 up, 4 down"), ("29", "pathway enrichments across KDA calls", "20 mtDNA, 9 nuclear")),
        "evidence_rows": (
            ("mtDNA OXPHOS", "99% up", "127 AD-up and 1 AD-down occurrence across eligible calls", "up"),
            ("Nuclear OXPHOS", "98% up", "239 AD-up and 4 AD-down occurrences across eligible calls", "up"),
            ("Fine excitatory neurons", "9/12 and 8/12", "mtDNA-up and nuclear-OXPHOS-up enrichment, respectively", "neutral"),
        ),
        "context_title": "Fine-cell evidence supports coordination, while broader tests qualify it",
        "context_subtitle": "The project treats fine-cell results as primary and direct broad-cell results as sensitivity evidence.",
        "context_cards": (
            card("Phase 11", "Excitatory localization", "Nine of 12 fine types enriched mtDNA-up and eight of 12 enriched nuclear OXPHOS-up.", "green"),
            card("Direct broad ROSMAP", "Only the nuclear side persists", "Excitatory nuclear OXPHOS remained strongly up, while the mtDNA component was not significant.", "gold"),
            card("SEA-AD", "Not evaluable", "No matching female ε2 category was active. Missing coverage adds no evidence for or against the finding.", "gray"),
        ),
        "context_bottom": "The coordinated two-genome claim rests mainly on fine-cell ROSMAP evidence.",
        "meaning_title": "Why this matters: an ε2-associated response may coordinate both OXPHOS genomes",
        "meaning_subtitle": "APOE ε2 lowers population risk, but a molecular pattern in diseased tissue can still reflect compensation or stress.",
        "meaning_cards": (
            card("Biological contrast", "Different from the male ε3/ε3 mismatch", "Both OXPHOS gene sets move upward instead of separating.", "blue"),
            card("Possible meaning", "Compensation or altered disease state", "The cells may increase respiratory instructions in response to inefficient mitochondria.", "green"),
            card("Required caution", "Protection is not established", "Population-level ε2 protection does not make this RNA pattern protective by itself.", "gold"),
        ),
        "meaning_bottom": "The result motivates a protective-response hypothesis but does not demonstrate a protective mechanism.",
        "not_proven": ("Higher OXPHOS protein, complex assembly, or ATP", "A female by ε2 disease interaction", "Independent replication across donors or cohorts"),
        "next_tests": ("Donor-level disease by sex by APOE interaction model", "APOE-isogenic female neuronal and glial models", "OXPHOS protein, ATP, respiration, and stress tolerance"),
        "literature": (
            literature("Belloy et al. 2019", "APOE allele risk", "Establishes large Alzheimer’s risk differences among APOE alleles.", "Does not explain the observed female ε2 RNA response.", "https://doi.org/10.1016/j.neuron.2019.03.075"),
            literature("Lee et al. 2023", "APOE and mitochondria", "Shows that APOE state can alter mitochondrial homeostasis.", "Uses a different APOE group and experimental context.", "https://doi.org/10.1016/j.celrep.2023.113183"),
            literature("Guo et al. 2023", "Sex-aware AD networks", "Supports analyzing Alzheimer’s biology by sex and cell type.", "Does not report this exact female ε2 program.", "https://doi.org/10.1186/s13024-023-00624-5"),
        ),
    },
    {
        "number": 4,
        "title": "Female APOE ε4 fine-cell results show a strong nuclear-OXPHOS decrease",
        "kind": "Mitochondrial DEG-program finding",
        "novelty": "Moderate",
        "divider_note": "The strongest signal is a fine-cell decrease in nuclear-encoded OXPHOS RNA.",
        "plain_title": "Female ε4 fine-cell results lower nuclear-encoded OXPHOS RNA in AD",
        "plain_subtitle": "The nuclear side is strongly downward, while mitochondrial-DNA OXPHOS genes show mixed directions.",
        "tags": ("Female", "APOE ε4", "Fine-cell primary", "Resolution-sensitive"),
        "concepts": (
            card("Nuclear OXPHOS", "206 of 216 down", "Most structural respiratory-complex subunits come from nuclear DNA.", "red"),
            card("mtDNA OXPHOS", "Mixed direction", "The mitochondrial genome contributes 26 up and 38 down occurrences.", "gold"),
            card("Interpretation", "Nuclear-sided decrease", "The result should not be described as a uniform decrease of all mitochondrial genes.", "blue"),
        ),
        "plain_bottom": "The finding is specific to fine-cell and KDA-aligned evidence because direct broad-cell results disagree.",
        "evidence_title": "ROSMAP: 95% of female ε4 nuclear-OXPHOS occurrences are AD-down",
        "evidence_subtitle": "The mtDNA component is smaller and more mixed than the nuclear component.",
        "metrics": (("216", "nuclear-OXPHOS occurrences", "10 up, 206 down"), ("64", "mtDNA-OXPHOS occurrences", "26 up, 38 down"), ("4/13", "excitatory fine types", "nuclear-down enrichment")),
        "evidence_rows": (
            ("Nuclear OXPHOS", "95% down", "Six eligible calls showed significant nuclear-OXPHOS enrichment", "down"),
            ("mtDNA OXPHOS", "59% down", "Ten calls showed significant enrichment, but direction was not uniform", "mixed"),
            ("Primary localization", "Excitatory fine types", "Four of 13 testable excitatory fine types enriched the nuclear-down program", "neutral"),
        ),
        "context_title": "Direct broad-cell results do not reproduce the female ε4 nuclear decrease",
        "context_subtitle": "This disagreement lowers confidence that the signal generalizes across resolutions.",
        "context_cards": (
            card("ROSMAP direct broad", "Weak positive, not significant", "Excitatory nuclear OXPHOS NES was +0.70 with local BH 0.991.", "gray"),
            card("SEA-AD direct broad", "Significant positive direction", "Excitatory nuclear OXPHOS NES was +2.01 with local BH 5.62 × 10⁻⁵.", "red"),
            card("SEA-AD fine-cell KDA", "Only one small astrocyte query", "Two genes overlapped and the corrected overlap test was not significant, BH 0.819.", "gold"),
        ),
        "context_bottom": "Describe this as a fine-cell female ε4 signal, not a broad-cell-wide effect.",
        "meaning_title": "Why this matters: most respiratory-complex instructions come from nuclear DNA",
        "meaning_subtitle": "A nuclear-sided reduction could reflect lower respiratory investment, stress, or a shift in cell state.",
        "meaning_cards": (
            card("Respiratory machinery", "Most subunits are nuclear-encoded", "A broad RNA decrease could affect the supply of respiratory-complex parts.", "red"),
            card("APOE context", "ε4 makes the hypothesis important", "APOE ε4 strongly increases late-onset Alzheimer’s risk at the population level.", "gold"),
            card("Resolution warning", "Broad-cell direction reverses", "Subtype composition or other aggregation effects may influence the fine-cell pattern.", "blue"),
        ),
        "meaning_bottom": "The fine-cell signal warrants follow-up, but the broad-cell disagreement must stay visible.",
        "not_proven": ("Reduced respiration, ATP, or respiratory-complex abundance", "A female by ε4 causal interaction", "A uniform decrease across all mitochondrial genes"),
        "next_tests": ("Show every contributing broad and fine cell type", "Fit donor-level disease by sex by ε4 interactions", "Measure respiratory-complex proteins and function"),
        "literature": (
            literature("Schmukler et al. 2020", "APOE4 and mitophagy", "Links APOE4 models to mitochondrial dynamics and mitophagy.", "Does not reproduce the nuclear-OXPHOS transcript pattern.", "https://doi.org/10.1038/s41419-020-02776-4"),
            literature("Lee et al. 2023", "APOE4 astrocytes", "Connects APOE4 state to impaired mitochondrial homeostasis.", "Different cell context and experimental design.", "https://doi.org/10.1016/j.celrep.2023.113183"),
            literature("Mathys et al. 2024", "Cell-resolved AD responses", "Supports strong differences among brain cell states.", "Uses ROSMAP and is not an independent replication.", "https://doi.org/10.1038/s41586-024-07606-7"),
        ),
    },
    {
        "number": 5,
        "title": "Male APOE ε2 cells show broad decreases across both OXPHOS genomes",
        "kind": "Mitochondrial DEG-program finding",
        "novelty": "High",
        "divider_note": "Both mtDNA and nuclear OXPHOS RNA are broadly lower, but query size strongly affects KDA yield.",
        "plain_title": "Male ε2 cells lower both mitochondrial and nuclear OXPHOS RNA in AD",
        "plain_subtitle": "This is the strongest coordinated downward OXPHOS pattern in ROSMAP.",
        "tags": ("Male", "APOE ε2", "Both genomes down", "Large queries"),
        "concepts": (
            card("mtDNA OXPHOS", "119 of 132 down", "About 90% of mitochondrial-genome OXPHOS occurrences were lower in AD.", "red"),
            card("Nuclear OXPHOS", "404 of 467 down", "About 87% of nuclear structural OXPHOS occurrences were lower in AD.", "red"),
            card("Key distinction", "Coordinated decrease", "Both genomes move downward, unlike a mitonuclear mismatch.", "blue"),
        ),
        "plain_bottom": "An ε2 allele can be protective at the population level while diseased tissue still shows an unfavorable-looking RNA pattern.",
        "evidence_title": "ROSMAP: male ε2 has the broadest downward OXPHOS burden",
        "evidence_subtitle": "Fine-cell pathway results and direct broad-cell sensitivity point mainly downward.",
        "metrics": (("132", "mtDNA-OXPHOS occurrences", "13 up, 119 down"), ("467", "nuclear-OXPHOS occurrences", "63 up, 404 down"), ("29", "fine-cell enrichments", "12 mtDNA, 17 nuclear")),
        "evidence_rows": (
            ("mtDNA OXPHOS", "90% down", "Thirteen eligible calls showed significant enrichment", "down"),
            ("Nuclear OXPHOS", "87% down", "Ten eligible calls showed significant enrichment", "down"),
            ("Excitatory fine types", "4/14 and 7/14", "mtDNA-down and nuclear-OXPHOS-down enrichment, respectively", "neutral"),
        ),
        "context_title": "Male ε2 has unusually large mitochondrial queries",
        "context_subtitle": "Query size can increase the number of network neighborhoods reached and drivers returned.",
        "context_cards": (
            card("Male ε2 median", "85 query genes", "The median eligible query was more than five times the overall median.", "red"),
            card("All eligible calls", "16.5 query genes", "The overall median shows how unusual the male ε2 query size was.", "blue"),
            card("SEA-AD", "Not evaluable", "No matching male ε2 category was active, so SEA-AD adds no evidence in either direction.", "gray"),
        ),
        "context_bottom": "Large queries confound KDA driver counts, although they do not automatically erase the DEG direction pattern.",
        "meaning_title": "Why this matters: molecular direction does not directly equal inherited risk",
        "meaning_subtitle": "The downward program could reflect respiratory reduction, altered cell state, or selective survival.",
        "meaning_cards": (
            card("Population genetics", "ε2 lowers average AD risk", "Risk protection does not predict every molecular state after disease develops.", "green"),
            card("Tissue biology", "Surviving cells may differ", "The observed nuclei may represent cells that persist under a particular disease state.", "gold"),
            card("Network interpretation", "Count of genes returned from KDA calls is confounded", "More query genes create more opportunities for a gene to be returned from a KDA call.", "red"),
        ),
        "meaning_bottom": "The DEG direction is interesting, while the unusually high KDA yield needs query-size matching.",
        "not_proven": ("Loss of mitochondrial function or ATP", "That APOE ε2 caused the downward program", "A male by ε2 interaction or stronger driver biology"),
        "next_tests": ("Repeat KDA with query sizes matched across groups", "Fit donor-aware sex and APOE interaction models", "Test respiratory proteins and function in male ε2 models"),
        "literature": (
            literature("Belloy et al. 2019", "APOE allele risk", "Establishes population-level protection associated with ε2.", "Does not predict the molecular state of diseased male ε2 cells.", "https://doi.org/10.1016/j.neuron.2019.03.075"),
            literature("Guo et al. 2023", "Sex-specific AD networks", "Supports sex-aware cell-resolved analysis.", "Does not report this exact male ε2 decrease.", "https://doi.org/10.1186/s13024-023-00624-5"),
            literature("Mathys et al. 2024", "Cell-state heterogeneity", "Shows that Alzheimer’s responses differ among brain cell populations.", "Uses ROSMAP and cannot independently validate this pattern.", "https://doi.org/10.1038/s41586-024-07606-7"),
        ),
    },
    {
        "number": 6,
        "title": "Male APOE ε4 cells show a weaker possible mitonuclear mismatch",
        "kind": "Mitochondrial DEG-program finding",
        "novelty": "Moderate",
        "divider_note": "mtDNA OXPHOS is mostly up and nuclear OXPHOS is modestly down, with mixed cross-cohort sensitivity.",
        "plain_title": "Male ε4 cells may separate mitochondrial and nuclear OXPHOS RNA directions",
        "plain_subtitle": "The direction split resembles male ε3/ε3, but the nuclear decrease is weaker and cross-cohort broad-cell evidence disagrees.",
        "tags": ("Male", "APOE ε4", "Possible mismatch", "Needs replication"),
        "concepts": (
            card("Mitochondrial DNA", "87 of 110 up", "mtDNA-encoded OXPHOS RNA mostly increases in AD.", "blue"),
            card("Nuclear DNA", "55 of 89 down", "Nuclear structural OXPHOS RNA leans downward, but less strongly.", "red"),
            card("Reading", "Weaker mismatch", "The two sides differ, but the evidence does not support a definitive mismatch claim.", "gold"),
        ),
        "plain_bottom": "The pattern is a provisional RNA-level hypothesis, not evidence of unbalanced respiratory proteins.",
        "evidence_title": "ROSMAP: male ε4 shows a clear mtDNA-up tendency and a modest nuclear-down tendency",
        "evidence_subtitle": "The nuclear direction is substantially less one-sided than in male ε3/ε3.",
        "metrics": (("110", "mtDNA-OXPHOS occurrences", "87 up, 23 down"), ("89", "nuclear-OXPHOS occurrences", "34 up, 55 down"), ("11/13", "excitatory fine types", "mtDNA-up enrichment")),
        "evidence_rows": (
            ("mtDNA OXPHOS", "79% up", "Fifteen eligible calls showed significant enrichment", "up"),
            ("Nuclear OXPHOS", "62% down", "Only three eligible calls showed significant enrichment", "down"),
            ("Strength of split", "Possible, not definitive", "The nuclear side is too mixed to match the strength of Finding 2", "mixed"),
        ),
        "context_title": "Direct broad-cell evidence agrees in ROSMAP but reverses in SEA-AD",
        "context_subtitle": "Cross-resolution disagreement keeps the male ε4 mismatch provisional.",
        "context_cards": (
            card("ROSMAP excitatory", "+2.03 mtDNA NES", "The mtDNA-up component survived composition adjustment.", "blue"),
            card("ROSMAP excitatory", "−1.72 nuclear NES", "The nuclear-down component also survived composition adjustment.", "red"),
            card("SEA-AD excitatory", "+2.46 nuclear NES", "SEA-AD showed the opposite nuclear direction and no active male ε4 fine-cell KDA query.", "gold"),
        ),
        "context_bottom": "The broad-cell mismatch is not robust across cohorts, and SEA-AD cannot test it at fine-cell KDA resolution.",
        "meaning_title": "Why this matters: a mismatch outside ε3/ε3 would broaden the hypothesis",
        "meaning_subtitle": "If confirmed, the split could represent a general male response or an APOE-dependent gradient.",
        "meaning_cards": (
            card("Comparison", "Related to Finding 2", "Both findings place mtDNA OXPHOS upward and nuclear OXPHOS downward.", "blue"),
            card("Difference", "The ε4 split is weaker", "The nuclear component contains many more up occurrences than the male ε3/ε3 result.", "gold"),
            card("Inference", "Direct comparisons are required", "Separate strata cannot distinguish a general male response from an APOE effect.", "red"),
        ),
        "meaning_bottom": "A prespecified balance score would test the strength of the split directly across groups.",
        "not_proven": ("A physical imbalance of OXPHOS proteins", "A male by ε4 disease interaction", "Cross-cohort robustness at broad or fine resolution"),
        "next_tests": ("Freeze a mitonuclear balance score before testing", "Compare male ε4 with male ε3/ε3 and female ε4", "Measure paired OXPHOS proteins and respiratory function"),
        "literature": (
            literature("Belloy et al. 2019", "APOE ε4 risk", "Establishes ε4 as a major common risk allele for late-onset AD.", "Risk association does not validate the RNA mismatch.", "https://doi.org/10.1016/j.neuron.2019.03.075"),
            literature("Lee et al. 2023", "APOE4 mitochondrial biology", "Shows that APOE4 can alter mitochondrial homeostasis.", "Uses astrocyte models rather than this male cell context.", "https://doi.org/10.1016/j.celrep.2023.113183"),
            literature("Guo et al. 2023", "Sex-aware networks", "Supports testing Alzheimer’s molecular patterns separately by sex.", "Does not establish the male ε4 mitonuclear split.", "https://doi.org/10.1186/s13024-023-00624-5"),
        ),
    },
    {
        "number": 7,
        "title": "A cytosolic-ribosome module repeatedly connects to mitochondrial OXPHOS",
        "kind": "Recurrent ROSMAP network-module finding",
        "novelty": "Moderate",
        "divider_note": "RPL11, RPS15, and related cytosolic ribosome genes recur near nuclear OXPHOS query genes.",
        "plain_title": "Cytosolic ribosome genes repeatedly connect to mitochondrial OXPHOS queries",
        "plain_subtitle": "The cytosolic ribosome builds most cellular proteins. The signal is more credible as one module than as 20 independent drivers.",
        "tags": ("20 ribosome genes", "19 categories", "RPL11 and RPS15", "Module-level claim"),
        "concepts": (
            card("Protein production", "Cytosolic ribosome", "This molecular machine builds most proteins outside mitochondria.", "blue"),
            card("Network neighborhood", "Nuclear OXPHOS", "Many returned ribosomal genes sit near nuclear genes that encode respiratory parts.", "green"),
            card("Interpretation", "One recurrent module", "Shared biology and network connectivity make the genes non-independent candidates.", "gold"),
        ),
        "plain_bottom": "The analysis prioritizes a ribosome-to-OXPHOS system, not 20 separate proven mitochondrial controllers.",
        "evidence_title": "ROSMAP: cytosolic ribosome genes are strongly over-represented among drivers",
        "evidence_subtitle": "The enrichment test compares 228 unique non-mitochondrial drivers with the exact network background.",
        "metrics": (("20/228", "driver genes in KEGG ribosome", "8.8% of drivers"), ("71/11,478", "ribosome genes in background", "0.62% of background"), ("3.56 × 10⁻¹⁵", "BH-adjusted enrichment", "one-sided hypergeometric")),
        "evidence_rows": (
            ("Category recurrence", "19 of 29", "Ribosome genes occur in 19 categories containing non-mitochondrial drivers", "neutral"),
            ("Category units", "70 of 381", "Ribosome genes comprise 18.4% of non-mitochondrial gene-by-category units", "neutral"),
            ("Within-call returns", "133 of 623", "Ribosome genes comprise 21.3% of non-mitochondrial returns", "neutral"),
        ),
        "context_title": "RPL11 and RPS15 anchor the recurrent ribosome module",
        "context_subtitle": "RPL11 has a broad nuclear-OXPHOS neighborhood, while RPS15 recurs across the most categories.",
        "context_cards": (
            card("RPL11 recurrence", "24 calls, 10 categories", "The calls span all six strata and four broad networks.", "blue"),
            card("RPL11 neighborhood", "253 overlaps, 37 genes", "Nuclear structural OXPHOS contributes 151 overlaps, including 100 AD-down occurrences.", "red"),
            card("RPS15 recurrence", "22 calls, 11 categories", "RPS15 is the most broadly recurrent individual representative.", "green"),
        ),
        "context_bottom": "Frequent RPL11 neighbors include COX7C, UQCRQ, NDUFS5, NDUFA1, ATP5PF, NDUFB9, and NDUFB3.",
        "meaning_title": "Why this matters: cellular protein production may track mitochondrial respiratory stress",
        "meaning_subtitle": "Ribosome stress and OXPHOS changes can be biologically linked, but network topology offers a technical alternative.",
        "meaning_cards": (
            card("Biological model", "Translation and respiration are coupled", "Cells must produce nuclear OXPHOS proteins before respiratory complexes can assemble.", "green"),
            card("Stress model", "RPL11 can signal ribosomal stress", "Experimental systems connect RPL11 with MDM2 and p53 signaling.", "gold"),
            card("Technical model", "Highly connected genes rank easily", "Abundant ribosomal genes may receive an advantage in network-based selection.", "red"),
        ),
        "meaning_bottom": "Degree-matched network tests are necessary before interpreting ribosomal recurrence as regulation.",
        "not_proven": ("That ribosomal proteins regulate their OXPHOS neighbors", "Independent replication across fine-cell calls", "That enrichment survives network-degree controls"),
        "next_tests": ("Use degree-matched randomized networks", "Repeat KDA after excluding cytosolic-ribosome nodes", "Perturb RPL11 or RPS15 and measure translation and respiration"),
        "literature": (
            literature("Ding et al. 2005", "Ribosome dysfunction in AD", "Reports impaired protein synthesis and RNA oxidation in human AD tissue.", "Does not establish the ROSMAP ribosome-to-OXPHOS network.", "https://doi.org/10.1523/JNEUROSCI.3040-05.2005"),
            literature("Zhang et al. 2003", "RPL11 stress signaling", "Shows that RPL11 can signal through the MDM2 and p53 pathway.", "Experimental stress biology does not prove mitochondrial regulation.", "https://doi.org/10.1128/MCB.23.23.8902-8912.2003"),
            literature("Current ROSMAP analysis", "Module recurrence", "Multiple ribosomal genes recur across categories and OXPHOS neighborhoods.", "Shared donors and network connectivity limit independence.", ""),
        ),
    },
    {
        "number": 8,
        "title": "LAMTOR5 links lysosomal nutrient sensing to OXPHOS",
        "kind": "Recurrent ROSMAP driver finding",
        "novelty": "High",
        "divider_note": "LAMTOR5 repeatedly links lysosomal nutrient sensing with mostly decreased nuclear OXPHOS genes.",
        "plain_title": "LAMTOR5 connects lysosomal nutrient sensing with mitochondrial energy genes",
        "plain_subtitle": "Lysosomes recycle cellular material and help sense nutrients. LAMTOR5 helps relay that information to mTORC1.",
        "tags": ("17 neuronal calls", "Six categories", "Lysosome and mTORC1", "Nuclear OXPHOS"),
        "concepts": (
            card("Lysosome", "Recycling and nutrient sensing", "The lysosome breaks down material and helps the cell judge nutrient availability.", "blue"),
            card("LAMTOR5", "Ragulator component", "LAMTOR5 helps connect amino-acid sensing at lysosomes to mTORC1 signaling.", "green"),
            card("Mitochondria", "Mostly decreased nuclear OXPHOS", "The network neighborhood suggests a connection with respiratory investment.", "red"),
        ),
        "plain_bottom": "The result proposes a lysosome-to-mitochondria bridge, while KDA cannot prove the direction of control.",
        "evidence_title": "ROSMAP: LAMTOR5 recurs in neuronal calls with coherent OXPHOS neighborhoods",
        "evidence_subtitle": "The strongest category scores occur in male ε2 neurons, where query size is unusually large.",
        "metrics": (("17", "supporting neuronal calls", "six categories, four strata"), ("87", "mitochondrial overlaps", "39 nuclear OXPHOS"), ("14/17", "enriched supporting queries", "nuclear OXPHOS")),
        "evidence_rows": (
            ("Nuclear OXPHOS", "30 of 39 down", "Most structural OXPHOS overlaps point toward lower RNA in AD", "down"),
            ("Frequent neighbors", "ATP5IF1, CHCHD10, ATP5MC2", "Additional repeated genes include NDUFA6, NDUFB6, TMEM11, and MRPL4", "neutral"),
            ("LAMTOR5 itself", "DEG in 11 of 17", "Up in female ε2 excitatory calls and down in the strongest male ε2 calls", "mixed"),
        ),
        "context_title": "Other drivers reinforce the lysosome and autophagy axis",
        "context_subtitle": "The broader module reduces reliance on a single LAMTOR5 result.",
        "context_cards": (
            card("GABARAPL2", "13 calls, five categories", "Its neighborhoods contain CHCHD2, ATP5MC3, PARK7, and mitochondrial-ribosome genes.", "green"),
            card("ATG101", "Six calls, three categories", "Its neighborhoods include MRPS34, UQCRFS1, CLPP, and PINK1.", "blue"),
            card("ATP6AP2", "Six calls, three categories", "It links V-ATPase biology with OXPHOS and mitochondrial protein import.", "gold"),
        ),
        "context_bottom": "SEA-AD had no active call in a matching LAMTOR5 discovery category, so exact-context support is unavailable.",
        "meaning_title": "Why this matters: nutrient sensing coordinates protein production and oxidative capacity",
        "meaning_subtitle": "LAMTOR5 sits in a plausible biological position between lysosomes, mTORC1, and mitochondria.",
        "meaning_cards": (
            card("Nutrient signal", "Amino acids activate mTORC1", "Ragulator helps position nutrient signaling at the lysosomal surface.", "blue"),
            card("Cellular response", "mTORC1 adjusts protein production", "This pathway can influence nuclear-encoded mitochondrial proteins and oxidative capacity.", "green"),
            card("AD relevance", "Aβ can disrupt this communication", "Experimental work links neuronal lysosome-to-mitochondria signaling with tau-dependent stress.", "gold"),
        ),
        "meaning_bottom": "Biological plausibility supports perturbation studies but does not validate the inferred LAMTOR5 edges.",
        "not_proven": ("Direct control of the listed OXPHOS genes in AD neurons", "That male ε2 recurrence is independent of large queries", "Final q-value significance for exploratory category scores"),
        "next_tests": ("Perturb LAMTOR5 in APOE-isogenic neurons", "Measure lysosomal acidity, mTORC1, and autophagic flow", "Measure OXPHOS proteins and respiration in the same cells"),
        "literature": (
            literature("Bar-Peled et al. 2012", "Ragulator and mTORC1", "Places LAMTOR5 in amino-acid sensing at the lysosome.", "Does not test Alzheimer’s neurons or OXPHOS neighbors.", "https://doi.org/10.1016/j.cell.2012.07.032"),
            literature("Morita et al. 2013", "mTORC1 and mitochondria", "Links mTORC1 with mitochondrial protein production and oxidative capacity.", "Does not establish LAMTOR5 as the causal node here.", "https://doi.org/10.1016/j.cmet.2013.10.001"),
            literature("Norambuena et al. 2018", "AD nutrient signaling", "Shows Aβ disruption of a neuronal lysosome-to-mitochondria pathway.", "LAMTOR5 was not manipulated in that study.", "https://doi.org/10.15252/embj.2018100241"),
        ),
    },
    {
        "number": 9,
        "title": "WDR82 is linked to a narrow excitatory-neuron mtDNA-up module",
        "kind": "Focused ROSMAP driver finding",
        "novelty": "High",
        "divider_note": "WDR82 appears only in excitatory neurons and sits near a four-gene mtDNA-up neighborhood.",
        "plain_title": "WDR82 sits near a focused mtDNA-up signal in excitatory neurons",
        "plain_subtitle": "The exact neighborhood is narrow, and four recurring mitochondrial genes begin within one long mitochondrial RNA.",
        "tags": ("Excitatory only", "18 KDA calls", "Four mtDNA genes", "Gene returned from KDA calls ≠ strong DEG"),
        "concepts": (
            card("WDR82", "Chromatin-associated candidate", "WDR82 participates in nuclear chromatin regulation rather than the mitochondrial ribosome.", "blue"),
            card("Exact neighborhood", "MT-ND1, ND3, ND4L, ND5", "These four mtDNA genes account for nearly every exact KDA overlap.", "green"),
            card("Dependence warning", "One long starting RNA", "The mitochondrial heavy strand produces a long RNA that is later cut into gene products.", "gold"),
        ),
        "plain_bottom": "Four gene names do not provide four independent regulatory observations when they share one starting transcript.",
        "evidence_title": "ROSMAP: every WDR82-supporting query contains an enriched mtDNA-up program",
        "evidence_subtitle": "KDA can nominate a gene by network position even when the candidate is not a strong DEG.",
        "metrics": (("18", "supporting excitatory calls", "four sex/APOE strata"), ("172", "mtDNA-OXPHOS occurrences", "all 172 AD-up"), ("18/18", "enriched input queries", "mtDNA OXPHOS")),
        "evidence_rows": (
            ("Exact KDA overlap", "68 of 70", "Occurrences are MT-ND1, MT-ND3, MT-ND4L, or MT-ND5", "up"),
            ("Other overlap", "2 of 70", "The only other exact overlap gene is PIM1", "neutral"),
            ("WDR82 expression", "0 of 18 paper DEGs", "Thirteen calls had FDR below 0.05, but effects stayed below the stored size threshold", "mixed"),
        ),
        "context_title": "WDR82 recurrence concentrates in female ε3/ε3 excitatory neurons",
        "context_subtitle": "The candidate appears in four strata but most supporting calls come from one group.",
        "context_cards": (
            card("Female ε2", "2 calls", "WDR82 appears in two excitatory fine-cell queries.", "blue"),
            card("Female ε3/ε3", "11 calls", "This group supplies most of the WDR82 recurrence and the strongest program support.", "green"),
            card("Male groups", "5 calls", "Two male ε3/ε3 and three male ε4 excitatory calls also return WDR82.", "gold"),
        ),
        "context_bottom": "SEA-AD could return WDR82 in 11 matching excitatory backgrounds but did not, although it supports the female ε3/ε3 mtDNA program.",
        "meaning_title": "Why this matters: a chromatin candidate may track mitochondrial RNA abundance",
        "meaning_subtitle": "The signal could reflect transcriptional coupling, global mitochondrial RNA, or network construction.",
        "meaning_cards": (
            card("Mechanistic hypothesis", "Nuclear chromatin state influences mtRNA", "WDR82 could indirectly affect mitochondrial programs through nuclear regulation.", "blue"),
            card("Alternative explanation", "Mitochondrial read fraction", "A repeated mtDNA cluster may track overall mitochondrial RNA abundance or sample quality.", "red"),
            card("Network explanation", "Four linked genes dominate", "The narrow neighborhood may amplify one polycistronic signal rather than four mechanisms.", "gold"),
        ),
        "meaning_bottom": "Removing mtDNA query genes is an important sensitivity test before mechanistic interpretation.",
        "not_proven": ("Direct WDR82 binding to mtDNA or control of mtRNA", "Four independent mitochondrial regulatory edges", "Cross-cohort driver replication in SEA-AD"),
        "next_tests": ("Repeat KDA without mtDNA-encoded query genes", "Control mitochondrial read fraction and RNA quality", "Perturb WDR82 and measure mtRNA, H3K4me3, and respiration"),
        "literature": (
            literature("Lee and Skalnik 2008", "WDR82 chromatin biology", "Places WDR82 in SETD1A/B complexes and H3K4 trimethylation.", "Provides no direct mitochondrial mechanism.", "https://doi.org/10.1128/MCB.01356-07"),
            literature("Mercer et al. 2011", "Mitochondrial RNA processing", "Shows that mtDNA genes begin within long polycistronic transcripts.", "Does not connect WDR82 with mitochondrial transcription.", "https://doi.org/10.1016/j.cell.2011.06.051"),
            literature("Zhu et al. 2015", "WDR82 in AD expression", "Reports increased WDR82 and hub status in bulk hippocampal reanalysis.", "Bulk reanalysis lacks cell-resolved external validation.", "https://doi.org/10.3892/mmr.2015.4271"),
        ),
    },
    {
        "number": 10,
        "title": "SELENOM links ER redox biology to mitochondrial protein production",
        "kind": "Recurrent ROSMAP driver finding",
        "novelty": "High",
        "divider_note": "SELENOM repeatedly sits near decreased mitochondrial-translation genes in neuronal queries.",
        "plain_title": "SELENOM connects ER redox control with mitochondrial protein production",
        "plain_subtitle": "The endoplasmic reticulum, or ER, folds many proteins and helps regulate calcium and oxidation.",
        "tags": ("12 neuronal KDA calls", "All six strata", "ER redox and calcium", "Mitochondrial translation"),
        "concepts": (
            card("SELENOM", "ER redox protein", "This selenium-containing protein helps regulate reversible oxidation inside the ER.", "blue"),
            card("Mitochondrial translation", "Protein production inside mitochondria", "Mitochondrial ribosomes and factors build the proteins encoded by mtDNA.", "green"),
            card("Observed link", "Translation genes mostly down", "The exact network neighborhood connects the ER candidate with lower mitochondrial protein-production RNA.", "red"),
        ),
        "plain_bottom": "SELENOM is not part of the mitochondrial ribosome. KDA links two cellular systems through network proximity.",
        "evidence_title": "ROSMAP: mitochondrial-translation genes dominate the SELENOM neighborhood",
        "evidence_subtitle": "The candidate recurs across groups, so the result is not sex- or APOE-specific.",
        "metrics": (("12", "supporting KDA calls", "10 excitatory, 2 inhibitory"), ("51", "mitochondrial overlaps", "27 translation genes"), ("11/12", "enriched input queries", "nuclear OXPHOS")),
        "evidence_rows": (
            ("Translation direction", "22 of 27 down", "Most mitochondrial-translation overlaps have lower RNA in AD", "down"),
            ("Repeated neighbors", "MRPS34, TUFM, MRPS7", "CLPP and MRPS26 also recur in the exact KDA neighborhood", "neutral"),
            ("SELENOM itself", "DEG in 10 of 12", "The gene returned from KDA calls also changes expression frequently", "mixed"),
        ),
        "context_title": "Cross-cohort and genetic evidence do not yet support SELENOM directly",
        "context_subtitle": "The ROSMAP recurrence and coherent neighborhood remain the main evidence.",
        "context_cards": (
            card("SEA-AD testability", "10 matching backgrounds", "SELENOM was available in all male ε3/ε3 excitatory networks.", "blue"),
            card("SEA-AD return", "0 of 10", "SELENOM was not returned from those SEA-AD KDA calls.", "gold"),
            card("Human genetics", "No direct support found", "The local genetic screen did not provide direct gene-level support for SELENOM.", "gray"),
        ),
        "context_bottom": "Lack of SEA-AD or genetic support lowers external confidence but does not erase recurrent ROSMAP evidence.",
        "meaning_title": "Why this matters: ER and mitochondrial stress responses depend on each other",
        "meaning_subtitle": "Calcium and oxidation move between the ER and mitochondria, influencing protein folding and energy production.",
        "meaning_cards": (
            card("ER function", "Protein folding and calcium", "Disrupted ER balance can alter cellular stress signaling.", "blue"),
            card("Mitochondrial function", "Translation supplies mtDNA proteins", "Lower translation machinery could affect respiratory-complex assembly.", "red"),
            card("Candidate mechanism", "Cross-organelle stress", "SELENOM could influence mitochondria indirectly through ER redox or calcium control.", "green"),
        ),
        "meaning_bottom": "A joint ER and mitochondrial perturbation experiment can distinguish specific coupling from general stress.",
        "not_proven": ("Direct SELENOM control of TUFM or MRPS proteins", "A causal effect on mitochondrial translation", "Independent human or genetic validation"),
        "next_tests": ("Perturb and rescue SELENOM in excitatory neurons", "Measure ER calcium and redox state", "Measure mitochondrial translation, OXPHOS proteins, and respiration"),
        "literature": (
            literature("Ferguson et al. 2006", "SELENOM molecular function", "Defines SELENOM as an ER-lumen thioredoxin-like oxidoreductase.", "Does not establish mitochondrial regulation in AD.", "https://doi.org/10.1074/jbc.M511386200"),
            literature("Yim et al. 2009", "Neuronal redox and calcium", "Connects SELENOM with neuronal redox and calcium regulation.", "Experimental evidence does not reproduce the human network.", "https://doi.org/10.3892/ijmm_00000211"),
            literature("Experimental Aβ study", "SELENOM and AD phenotypes", "Reports effects on Aβ-related and mitochondrial phenotypes in models.", "Model-system evidence does not prove the ROSMAP edges.", "https://doi.org/10.3390/ijms14034385"),
        ),
    },
    {
        "number": 11,
        "title": "SELENOW connects redox and protein-quality control to respiration",
        "kind": "Recurrent ROSMAP driver finding",
        "novelty": "Moderate",
        "divider_note": "SELENOW has a broad mitochondrial neighborhood spanning respiration, translation, and protein quality control.",
        "plain_title": "SELENOW connects redox balance and mitochondrial protein quality with respiration",
        "plain_subtitle": "Redox balance keeps oxidation within a range the cell can tolerate. SELENOW should not be treated as the same mechanism as SELENOM.",
        "tags": ("16 neuronal calls", "Six categories", "Redox biology", "Broad mitochondrial neighborhood"),
        "concepts": (
            card("Respiration", "NDUFB11, COA3, CYC1", "These genes support respiratory-complex function.", "blue"),
            card("Protein production", "MRPS34 and MRPL34", "These genes help mitochondria make their own encoded proteins.", "green"),
            card("Quality control", "CLPP and membrane genes", "Damaged mitochondrial proteins and inner-membrane transport also appear in the neighborhood.", "gold"),
        ),
        "plain_bottom": "The broad neighborhood suggests a redox and proteostasis system rather than one narrow OXPHOS edge.",
        "evidence_title": "ROSMAP: SELENOW recurs across neuronal contexts with 123 mitochondrial overlaps",
        "evidence_subtitle": "The supporting calls cover excitatory and inhibitory neurons in four sex/APOE strata.",
        "metrics": (("16", "supporting neuronal calls", "six categories, four strata"), ("123", "mitochondrial overlaps", "multiple mitochondrial systems"), ("13/16", "enriched input queries", "nuclear OXPHOS")),
        "evidence_rows": (
            ("Respiration", "NDUFB11, COA3, CYC1", "Repeated neighbors support respiratory-complex biology", "neutral"),
            ("Translation and quality", "MRPS34, MRPL34, CLPP", "The neighborhood includes mitochondrial ribosomes and damaged-protein removal", "neutral"),
            ("SELENOW itself", "DEG in 10 of 16", "The driver frequently changes expression in its supporting calls", "mixed"),
        ),
        "context_title": "SEA-AD adds a weak selenium-theme signal, not SELENOW replication",
        "context_subtitle": "Exact-gene support and pathway-theme support represent different evidence levels.",
        "context_cards": (
            card("SEA-AD excitatory", "0 of 10 returned", "SELENOW was available but not selected in matching male ε3/ε3 excitatory calls.", "gold"),
            card("SEA-AD inhibitory", "0 of 8 returned", "SELENOW was also available but not selected in matched inhibitory calls.", "gold"),
            card("Related SEA candidate", "SECISBP2 returned once", "A different selenium-related gene provides only weak thematic support.", "blue"),
        ),
        "context_bottom": "The local genetic screen adds weak transcriptome-wide association support but does not establish causality.",
        "meaning_title": "Why this matters: redox balance, tau clearance, and mitochondrial function may converge",
        "meaning_subtitle": "Prior experiments connect SELENOW with respiration in immune cells and tau clearance in an AD mouse model.",
        "meaning_cards": (
            card("Redox control", "Mitochondria both use and shape redox state", "Oxidative imbalance can damage proteins and respiratory machinery.", "blue"),
            card("Protein quality", "CLPP and tau-related evidence", "The candidate may connect mitochondrial protein cleanup with broader proteostasis.", "green"),
            card("Cell-context caveat", "Prior models differ", "Macrophage and mouse evidence cannot establish a human neuronal mechanism.", "gold"),
        ),
        "meaning_bottom": "SELENOW and SELENOM share selenium biology but have different neighborhoods and must remain separate hypotheses.",
        "not_proven": ("Control of the listed mitochondrial genes in human neurons", "Exact cell, sex, or APOE replication", "That weak genetic or selenium-theme evidence is causal"),
        "next_tests": ("Perturb SELENOW in excitatory and inhibitory neurons", "Measure tau clearance, redox state, and protein quality", "Compare normal SELENOW with a redox-inactive version"),
        "literature": (
            literature("Misra et al. 2023", "SELENOW and respiration", "Shows that SELENOW loss alters redox state and mitochondrial respiration.", "The experiment used macrophages rather than neurons.", "https://doi.org/10.1016/j.redox.2022.102571"),
            literature("Ren et al. 2024", "SELENOW and tau", "Reports improved tau clearance and phenotypes after SELENOW overexpression.", "Evidence comes from a 3×Tg-AD mouse model.", "https://doi.org/10.1038/s42003-024-06572-0"),
            literature("Current ROSMAP analysis", "Human neuronal neighborhood", "Adds cell-resolved links to respiration and mitochondrial quality control.", "KDA does not prove direction or causality.", ""),
        ),
    },
    {
        "number": 12,
        "title": "PGK1 links astrocyte glycolysis and hypoxia signaling to mitochondrial quality control",
        "kind": "Focused ROSMAP astrocyte-driver finding",
        "novelty": "Moderate",
        "divider_note": "PGK1 connects astrocyte glycolysis with a narrow BNIP3, BNIP3L, and FAM162A stress neighborhood.",
        "plain_title": "PGK1 links astrocyte sugar breakdown with removal of damaged mitochondria",
        "plain_subtitle": "Glycolysis makes energy from sugar outside mitochondria. Mitophagy is the recycling of damaged mitochondria.",
        "tags": ("Astrocytes", "Three calls", "Glycolysis", "Hypoxia and mitophagy"),
        "concepts": (
            card("PGK1", "Glycolysis gene", "PGK1 participates in the pathway that breaks down glucose outside mitochondria.", "blue"),
            card("Stress neighborhood", "FAM162A and BNIP3", "These genes respond to low oxygen and mitochondrial damage.", "red"),
            card("Mitochondrial cleanup", "BNIP3L", "BNIP3L can help mark damaged mitochondria for recycling.", "green"),
        ),
        "plain_bottom": "The focused neighborhood suggests a glycolysis-to-mitophagy hypothesis, not broad control of all OXPHOS genes.",
        "evidence_title": "ROSMAP: PGK1 appears in three astrocyte contexts with a three-gene neighborhood",
        "evidence_subtitle": "The category scores rank candidates but are exploratory rather than final q-values.",
        "metrics": (("3", "supporting astrocyte calls", "F_e33, F_e4, M_e4"), ("8", "exact overlap occurrences", "three genes"), ("3", "neighbor genes", "FAM162A, BNIP3, BNIP3L")),
        "evidence_rows": (
            ("Female ε3/ε3", "logFC +1.06", "PGK1 was AD-up and met the report’s DEG threshold", "up"),
            ("Female ε4", "logFC +0.03", "PGK1 showed almost no expression change and was not a paper DEG", "mixed"),
            ("Male ε4", "logFC +0.95", "PGK1 was AD-up and met the report’s DEG threshold", "up"),
        ),
        "context_title": "The neighborhood is specific, while external support remains limited",
        "context_subtitle": "A narrow module can sharpen a hypothesis but also depends heavily on a few genes.",
        "context_cards": (
            card("Exact overlap", "FAM162A 3, BNIP3 3, BNIP3L 2", "All eight exact occurrences belong to the hypoxia and mitochondrial-quality theme.", "green"),
            card("SEA-AD", "Present but not returned", "PGK1 was available in the only active female ε4 astrocyte network, whose query had only five genes.", "gold"),
            card("Discovery overlap", "Mathys et al. uses ROSMAP", "Related glial glycolysis evidence may share donors and is not independent validation.", "gray"),
        ),
        "context_bottom": "The candidate appears across several groups and should not be labeled sex- or APOE-specific.",
        "meaning_title": "Why this matters: astrocytes can rebalance glycolysis and mitochondrial cleanup",
        "meaning_subtitle": "Astrocytes help regulate energy supply for neurons and respond strongly to Alzheimer’s pathology.",
        "meaning_cards": (
            card("Energy routing", "More glycolysis may reduce mitochondrial demand", "Cells can shift ATP production toward glucose breakdown outside mitochondria.", "blue"),
            card("Damage response", "BNIP3 and BNIP3L mark stress", "Hypoxia-responsive genes can participate in removing damaged mitochondria.", "green"),
            card("Ambiguous consequence", "Adaptive or harmful", "Increased glycolysis and mitophagy can protect cells or mark severe stress.", "gold"),
        ),
        "meaning_bottom": "A perturbation and rescue design can test whether PGK1 acts upstream of the BNIP3 pathway.",
        "not_proven": ("That PGK1 activates BNIP3 or BNIP3L", "Whether glycolysis is adaptive or harmful", "Independent SEA-AD or donor-independent validation"),
        "next_tests": ("Perturb PGK1 in APOE-isogenic astrocytes", "Measure glycolytic rate and mitophagic flow", "Block or rescue BNIP3 and BNIP3L while measuring respiration"),
        "literature": (
            literature("Mathys et al. 2024", "Glial glycolytic remodeling", "Reports glial glycolysis modules containing PGK1 and BNIP3L in human AD.", "Uses ROSMAP, so donor overlap must be checked.", "https://doi.org/10.1038/s41586-024-07606-7"),
            literature("Schmukler et al. 2020", "APOE4 astrocyte mitophagy", "Links APOE4 astrocytes with altered mitochondrial dynamics and mitophagy.", "Does not demonstrate PGK1 control of BNIP3 genes.", "https://doi.org/10.1038/s41419-020-02776-4"),
            literature("Lee et al. 2023", "Astrocyte mitochondrial clearance", "Connects lysosomal cholesterol with impaired mitochondrial clearance and respiration.", "Uses an experimental APOE4 model rather than these three groups.", "https://doi.org/10.1016/j.celrep.2023.113183"),
        ),
    },
    {
        "number": 13,
        "title": "An OPC FTL and ANKRD11 module links iron handling, GPX4, and autophagy",
        "kind": "Focused ROSMAP OPC-module finding",
        "novelty": "High",
        "divider_note": "FTL and ANKRD11 share an OPC neighborhood involving iron storage, GPX4, OXPHOS, and autophagy.",
        "plain_title": "An OPC module links iron storage with mitochondrial protection and cleanup",
        "plain_subtitle": "OPCs mature into myelin-producing cells. Ferroptosis is cell death caused by iron-dependent damage to membrane fats.",
        "tags": ("OPCs", "FTL and ANKRD11", "Iron and GPX4", "Ferroptosis not proven"),
        "concepts": (
            card("Iron storage", "FTL and FTH1", "Ferritin stores iron in a safer form and limits damaging free iron.", "blue"),
            card("Lipid protection", "GPX4", "GPX4 helps prevent oxidation of membrane fats.", "green"),
            card("Mitochondrial cleanup", "Autophagy and stress genes", "FIS1, PARK7, and PHB2 connect the neighborhood with mitochondrial quality control.", "gold"),
        ),
        "plain_bottom": "The evidence supports an iron and autophagy hypothesis. Ferroptosis requires direct lipid-damage and rescue measurements.",
        "evidence_title": "ROSMAP: FTL and ANKRD11 share nearly identical OPC neighborhoods",
        "evidence_subtitle": "ROSMAP contains one OPC fine type, so the two group-specific calls do not provide broad subtype replication.",
        "metrics": (("2", "supporting OPC calls", "F_e33 and M_e2"), ("4", "shared core neighbors", "FTH1, GPX4, COX5B, UQCR10"), ("2/2", "queries enriched", "mtDNA and nuclear OXPHOS")),
        "evidence_rows": (
            ("Female ε3/ε3", "FTL up", "FTL met the DEG threshold in the shared OPC fine type", "up"),
            ("Male ε2", "FTL down", "FTL changed in the opposite direction in the male ε2 call", "down"),
            ("ANKRD11", "Effect threshold only in M_e2", "The current network cannot establish whether ANKRD11 or FTL is upstream", "mixed"),
        ),
        "context_title": "OPC driver enrichment highlights autophagy and iron handling",
        "context_subtitle": "The pathway terms overlap and partly depend on generic ubiquitin and tubulin genes.",
        "context_cards": (
            card("Selective autophagy", "BH 9.00 × 10⁻⁵", "This is the strongest exploratory OPC-driver pathway result.", "green"),
            card("Mitophagy", "BH 0.00233", "The driver list contains genes associated with mitochondrial cleanup.", "blue"),
            card("Iron uptake and transport", "BH 0.00968", "FTL, UBB, and UBC contribute to this pathway term.", "gold"),
        ),
        "context_bottom": "SEA-AD had no active OPC category, so the finding is not evaluable in that cohort.",
        "meaning_title": "Why this matters: OPCs may be vulnerable to iron-dependent lipid damage",
        "meaning_subtitle": "Iron storage, GPX4 protection, and mitochondrial quality control converge on a testable vulnerability model.",
        "meaning_cards": (
            card("Iron pressure", "Free iron can promote oxidation", "Ferritin changes may indicate altered iron storage or a compensatory response.", "red"),
            card("Membrane defense", "GPX4 limits lipid damage", "Reduced GPX4 activity can make OPCs vulnerable to iron-dependent injury.", "green"),
            card("Mechanistic threshold", "Rescue defines ferroptosis", "A ferroptosis inhibitor must rescue lipid damage and survival before using that label.", "gold"),
        ),
        "meaning_bottom": "Opposite FTL directions warn against one simple model across sex/APOE groups.",
        "not_proven": ("Ferroptosis in human AD OPCs", "A direct ANKRD11 to ferritin or GPX4 mechanism", "Independent recurrence of FTL and ANKRD11 modules"),
        "next_tests": ("Measure free iron, oxidized lipids, and lipid ROS", "Measure GPX4 activity and OPC survival", "Test ferroptosis rescue and perturb FTL and ANKRD11 separately"),
        "literature": (
            literature("OPC ferroptosis study", "GPX4-dependent OPC vulnerability", "Shows that impaired GPX4 protection can expose OPCs to iron-dependent lipid damage.", "Experimental OPC vulnerability does not prove human AD ferroptosis.", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8941078/"),
            literature("BMC Biology 2025", "Ferroptosis signatures in AD", "Reports oxytosis and ferroptosis-related transcriptomic signatures in AD datasets.", "A transcriptomic signature is not direct cell-death evidence.", "https://doi.org/10.1186/s12915-025-02235-6"),
            literature("Current ROSMAP analysis", "Human OPC network module", "Adds a focused FTL, ANKRD11, GPX4, and autophagy neighborhood.", "Only one OPC fine type contributes to the result.", ""),
        ),
    },
    {
        "number": 14,
        "title": "PLCG2 is genetically important but its KDA neighborhood is fragile",
        "kind": "Genetically supported, low-confidence network finding",
        "novelty": "High, with low network confidence",
        "divider_note": "PLCG2 has strong Alzheimer’s genetics, but every exact mitochondrial KDA overlap is MT-CO1 alone.",
        "plain_title": "PLCG2 has strong genetic support but a one-gene mitochondrial neighborhood",
        "plain_subtitle": "PLCG2 encodes a signaling enzyme. KDA selects network position, so a driver does not need to be a DEG.",
        "tags": ("Female inhibitory neurons", "Six calls", "MT-CO1 only", "Strong gene-level genetics"),
        "concepts": (
            card("Why PLCG2 matters", "Established AD genetics", "Human variants make PLCG2 an important Alzheimer’s candidate.", "green"),
            card("What KDA found", "Six female inhibitory calls", "The candidate appears in ε2, ε3/ε3, and ε4 female groups.", "blue"),
            card("Why the edge is fragile", "One repeated neighbor", "Every exact mitochondrial overlap is MT-CO1 rather than a broad neighborhood.", "red"),
        ),
        "plain_bottom": "Strong genetics supports the gene, but it does not validate this inhibitory-neuron network edge.",
        "evidence_title": "ROSMAP: PLCG2 repeats across six calls, but the exact overlap never broadens",
        "evidence_subtitle": "Repeated MT-CO1 is not equivalent to several distinct mitochondrial neighbors.",
        "metrics": (("6", "supporting inhibitory calls", "all in female strata"), ("1", "unique exact overlap gene", "MT-CO1"), ("0/6", "PLCG2 paper DEGs", "network nomination only")),
        "evidence_rows": (
            ("Female ε2", "1 call", "The exact mitochondrial overlap is MT-CO1", "neutral"),
            ("Female ε3/ε3", "4 calls", "All four calls repeat MT-CO1 as the exact overlap", "neutral"),
            ("Female ε4", "1 call", "Five MT-CO1 overlaps are AD-up overall and one is AD-down", "mixed"),
        ),
        "context_title": "The broader queries support mtDNA OXPHOS, but not a PLCG2 mechanism",
        "context_subtitle": "Input-query coherence and exact driver neighborhoods answer different questions.",
        "context_cards": (
            card("Supporting queries", "41 mtDNA occurrences", "The six full queries contain 36 AD-up and five AD-down mtDNA-OXPHOS occurrences.", "blue"),
            card("Program enrichment", "6 of 6 calls", "All six input queries show significant mtDNA-OXPHOS enrichment.", "green"),
            card("SEA-AD", "Not evaluable", "No female inhibitory category was active, so exact-context support is unavailable.", "gray"),
        ),
        "context_bottom": "Phase 19b supports PLCG2 at the gene level, while the MT-CO1 network edge remains technically narrow.",
        "meaning_title": "Why this matters: genetic credibility and network credibility must stay separate",
        "meaning_subtitle": "A well-established disease gene can still have an uncertain cell context or network neighborhood.",
        "meaning_cards": (
            card("Genetic evidence", "PLCG2 affects AD risk", "The protective P522R variant slightly increases a PLCG2 function.", "green"),
            card("Cell-context question", "Unexpected inhibitory-neuron signal", "PLCG2 has historically received more attention in microglia and dentate granule cells.", "gold"),
            card("Network question", "MT-CO1 may be fragile", "Ambient RNA, mixed droplets, labels, or connectivity could contribute to the repeated edge.", "red"),
        ),
        "meaning_bottom": "PLCG2 remains worth testing, but the first priority is verifying its neuronal presence and neighborhood.",
        "not_proven": ("That genetics validates the inhibitory-neuron edge", "A broad PLCG2 mitochondrial mechanism", "A female-specific PLCG2 disease interaction"),
        "next_tests": ("Confirm PLCG2 RNA and protein by spatial or in situ methods", "Perturb PLCG2 in validated neuronal models", "Measure MT-CO1, other mtRNAs, synapses, and respiration"),
        "literature": (
            literature("Phase 19b genetic screen", "Human gene-level support", "Provides strong local Alzheimer’s support for PLCG2.", "Gene-level support does not validate cell context or network edges.", ""),
            literature("PLCG2 P522R study 2019", "Protective weak hypermorph", "Shows that the protective variant slightly increases a PLCG2 function.", "Variant biology does not establish the MT-CO1 relationship.", "https://doi.org/10.1186/s13195-019-0469-0"),
            literature("Nature Genetics 2026", "Neuron-intrinsic PLCG2", "Reports neuronal PLCG2 effects on synapses, Aβ, and tau.", "Does not validate a PLCG2 to MT-CO1 regulatory edge.", "https://doi.org/10.1038/s41588-026-02709-5"),
        ),
    },
    {
        "number": 15,
        "title": "Astrocyte APOE is context-dependent, not an ε4-only driver",
        "kind": "Context-dependent ROSMAP astrocyte-driver finding",
        "novelty": "Moderate",
        "divider_note": "APOE is returned in three astrocyte groups with opposite expression directions and different mitochondrial neighbors.",
        "plain_title": "Astrocyte APOE changes direction across sex and genotype contexts",
        "plain_subtitle": "Astrocytes produce much of the brain’s APOE. Finding the gene in an APOE-stratified analysis does not make the result ε4-specific.",
        "tags": ("Astrocytes", "Three groups", "Opposite directions", "Not ε4-only"),
        "concepts": (
            card("Female ε2", "APOE up", "APOE logFC is +0.79 in the supporting astrocyte call.", "green"),
            card("Male ε2", "APOE down", "APOE logFC is −0.51 in the supporting astrocyte call.", "red"),
            card("Male ε4", "APOE down", "APOE logFC is −1.25 in the supporting astrocyte call.", "red"),
        ),
        "plain_bottom": "Opposite within-group directions motivate a direct interaction test rather than an ε4-only story.",
        "evidence_title": "ROSMAP: APOE is a DEG and KDA candidate in three astrocyte contexts",
        "evidence_subtitle": "Each context contributes one call, so the evidence is too sparse to define one shared module.",
        "metrics": (("3", "supporting astrocyte calls", "F_e2, M_e2, M_e4"), ("3/3", "APOE paper DEGs", "one up, two down"), ("5", "named mitochondrial neighbors", "across the three calls")),
        "evidence_rows": (
            ("Protein production", "TUFM", "A mitochondrial translation factor appears in the APOE neighborhoods", "neutral"),
            ("Energy and structure", "LDHB and CHCHD10", "The neighbors span metabolism and mitochondrial structure or stress", "neutral"),
            ("ATP synthase", "ATP5PB and ATP5F1A", "Nuclear-encoded respiratory-complex genes also appear", "neutral"),
        ),
        "context_title": "The APOE neighborhoods vary rather than forming one repeated pathway",
        "context_subtitle": "Different directions and neighbors may reflect true context or cell-state and sampling differences.",
        "context_cards": (
            card("Direction", "+0.79 in F_e2", "The female ε2 astrocyte call shows higher APOE RNA in AD.", "green"),
            card("Direction", "−0.51 and −1.25", "The male ε2 and male ε4 astrocyte calls show lower APOE RNA in AD.", "red"),
            card("SEA-AD", "Not evaluable", "None of the three matching categories was active in the supplemental cohort.", "gray"),
        ),
        "context_bottom": "The human genetic importance of APOE does not validate the direction differences or mitochondrial edges.",
        "meaning_title": "Why this matters: APOE biology depends on the cellular and genetic context",
        "meaning_subtitle": "The same gene may respond differently across groups even when its population-level risk role is well established.",
        "meaning_cards": (
            card("Cell source", "Astrocytes produce APOE", "The cell class makes the candidate biologically plausible.", "blue"),
            card("Disease response", "Direction changes by group", "APOE RNA may reflect different astrocyte states or responses to pathology.", "gold"),
            card("Inference limit", "Separate tests do not show interaction", "A formal model must compare disease effects across sex and genotype groups.", "red"),
        ),
        "meaning_bottom": "The result argues for context-specific APOE models rather than an ε4-only interpretation.",
        "not_proven": ("That APOE regulates the neighboring mitochondrial genes", "One shared astrocyte module across groups", "A sex or genotype interaction from three separate calls"),
        "next_tests": ("Fit disease by sex by APOE models for astrocyte APOE", "Use APOE-isogenic astrocytes", "Measure lipid handling, neighboring proteins, and mitochondrial function"),
        "literature": (
            literature("Belloy et al. 2019", "APOE and AD risk", "Establishes APOE as the strongest common late-onset AD risk locus.", "Genetics does not validate these three network neighborhoods.", "https://doi.org/10.1016/j.neuron.2019.03.075"),
            literature("Lee et al. 2023", "APOE4 astrocyte biology", "Shows that astrocyte APOE state can alter mitochondrial homeostasis.", "Does not explain opposite directions across these groups.", "https://doi.org/10.1016/j.celrep.2023.113183"),
            literature("Schmukler et al. 2020", "APOE4 and mitophagy", "Connects APOE4 astrocytes with mitochondrial dynamics and cleanup.", "The current KDA result also includes ε2 groups.", "https://doi.org/10.1038/s41419-020-02776-4"),
        ),
    },
    {
        "number": 16,
        "title": "Female APOE ε4 vascular cells show a small heat-shock module",
        "kind": "Preliminary ROSMAP vascular-module finding",
        "novelty": "Moderate",
        "divider_note": "Three stress-response drivers define a small female ε4 vascular module across only two eligible calls.",
        "plain_title": "Female ε4 vascular cells prioritize a small protein-stress module",
        "plain_subtitle": "Heat-shock genes protect protein folding during many forms of cell stress. Literal high temperature is not required.",
        "tags": ("Female", "APOE ε4", "Vascular cells", "Two eligible calls"),
        "concepts": (
            card("HSPA1A", "Stress-response chaperone", "Helps proteins fold correctly or recover after stress.", "blue"),
            card("HSPH1", "Protein-recovery chaperone", "Works with other heat-shock proteins to protect damaged proteins.", "green"),
            card("PTGES3", "Chaperone-related protein", "Has protein-folding functions in addition to its other cellular roles.", "gold"),
        ),
        "plain_bottom": "Three related genes create a focused clue, not evidence of a broad vascular stress program.",
        "evidence_title": "ROSMAP: three of five female ε4 vascular candidates are stress-response genes",
        "evidence_subtitle": "The pathway analysis uses the vascular network background and remains exploratory.",
        "metrics": (("5", "unique non-MT vascular drivers", "female ε4"), ("3", "stress-response drivers", "HSPH1, HSPA1A, PTGES3"), ("2", "eligible vascular calls", "small evidence base")),
        "evidence_rows": (
            ("HSF1 activation", "BH 4.07 × 10⁻⁴", "HSF1 regulates many heat-shock response genes", "neutral"),
            ("Cellular heat response", "BH 0.00383", "The term reflects shared stress machinery, not necessarily temperature", "neutral"),
            ("Pathway dependence", "Three genes", "Related terms overlap and are driven by a very small candidate set", "mixed"),
        ),
        "context_title": "Small call count and missing SEA-AD coverage keep the module preliminary",
        "context_subtitle": "The evidence level reflects internal sparsity rather than a failed external comparison.",
        "context_cards": (
            card("ROSMAP coverage", "Two eligible calls", "Very few fine-cell comparisons contribute to the vascular result.", "red"),
            card("Pathway overlap", "Related terms share genes", "HSF1 activation and heat-response pathways are not independent findings.", "gold"),
            card("SEA-AD", "No active vascular category", "The supplemental cohort cannot evaluate this context.", "gray"),
        ),
        "context_bottom": "The candidate remains a low-confidence ROSMAP clue because of sparse internal support.",
        "meaning_title": "Why this matters: vascular cells protect blood flow and the blood-brain barrier",
        "meaning_subtitle": "A protein-protection response could mark vascular strain near Alzheimer’s pathology.",
        "meaning_cards": (
            card("Vascular role", "Maintain brain circulation", "Vascular cells help regulate blood flow and barrier function.", "blue"),
            card("Stress response", "Chaperones protect proteins", "The module may reflect protein damage or a general protective reaction.", "green"),
            card("Unknown trigger", "Many stresses activate HSF1", "Inflammation, oxidative stress, or other insults could produce the same genes.", "gold"),
        ),
        "meaning_bottom": "Spatial evidence can test whether the stress proteins rise near vascular Alzheimer’s pathology.",
        "not_proven": ("The type of stress that activated the genes", "A broad or sustained vascular response", "A female by ε4 disease interaction"),
        "next_tests": ("Confirm the module in donor-level vascular data", "Fit direct disease by sex by ε4 interactions", "Measure HSF1 targets spatially near brain vessels"),
        "literature": (
            literature("Current network ORA", "HSF1 activation", "Shows enrichment of a focused stress-response pathway in female ε4 vascular drivers.", "Only three related genes and two calls drive the result.", ""),
            literature("Guo et al. 2023", "Cell- and sex-aware AD networks", "Supports resolving Alzheimer’s responses by cell type and sex.", "Does not report this vascular heat-shock module.", "https://doi.org/10.1186/s13024-023-00624-5"),
            literature("Mathys et al. 2024", "Cell-resolved AD heterogeneity", "Shows that disease-associated states differ across brain cell populations.", "Uses ROSMAP and does not independently replicate this module.", "https://doi.org/10.1038/s41586-024-07606-7"),
        ),
    },
    {
        "number": 17,
        "title": "SEA-AD provides program and cross-context support despite no exact driver matches",
        "kind": "Cross-cohort reproducibility finding",
        "novelty": "Moderate and analytical",
        "divider_note": "Programs agree more strongly than exact driver identities across the two cohort-specific network analyses.",
        "plain_title": "ROSMAP and SEA-AD agree more on mitochondrial programs than on exact drivers",
        "plain_subtitle": "Exact context means the same gene, sex/APOE group, and broad cell class in both cohorts.",
        "tags": ("ROSMAP discovery", "SEA-AD support", "Zero exact non-MT matches", "Three relaxed matches"),
        "concepts": (
            card("Strict comparison", "Same gene and same context", "No directly testable non-mitochondrial driver met this strongest support tier.", "red"),
            card("Relaxed comparison", "Same gene in another context", "LAGE3, MIPOL1, and PAPOLA recur across cohorts in partially matched settings.", "gold"),
            card("Program comparison", "Mitochondrial patterns recur", "Female ε3/ε3 and male ε3/ε3 program evidence remains the strongest cross-cohort result.", "green"),
        ),
        "plain_bottom": "Different cohort-specific networks can nominate different genes even when they point to similar mitochondrial biology.",
        "evidence_title": "Exact matching had little opportunity and produced zero non-MT driver matches",
        "evidence_subtitle": "A gene absent from the matching SEA-AD network background could never be selected.",
        "metrics": (("83", "ROSMAP units in testable categories", "structural opportunity"), ("72", "units with gene in SEA background", "genuine KDA opportunity"), ("0", "exact same-context returns", "non-mitochondrial drivers")),
        "evidence_rows": (
            ("Gene-category opportunities", "12,941", "Intersected non-mitochondrial opportunities across matching contexts", "neutral"),
            ("Expected exact matches", "0.173", "Random expectation was already far below one exact match", "neutral"),
            ("One-sided test", "P = 1", "Zero exact matches is not evidence of active disagreement", "mixed"),
        ),
        "context_title": "Three genes provide context-relaxed cross-cohort support",
        "context_subtitle": "The recurrences support general candidate relevance but do not confirm the original sex/APOE and cell context.",
        "context_cards": (
            card("LAGE3", "Different group and neuron class", "ROSMAP excitatory recurrence and SEA male ε3/ε3 inhibitory recurrence. The SEA neighborhood is mitochondrial.", "blue"),
            card("MIPOL1", "Same male ε3/ε3 stratum", "The broad neuronal class differs, giving the closest partial context match.", "green"),
            card("PAPOLA", "Related glial lineage", "ROSMAP OPC and SEA oligodendrocyte results share lineage but not sex/APOE context.", "gold"),
        ),
        "context_bottom": "Across all genes, 3 of 43 SEA-AD drivers overlap 228 ROSMAP drivers, odds ratio 3.15 and P 0.0812.",
        "meaning_title": "Why this matters: pathway agreement can survive driver-ranking differences",
        "meaning_subtitle": "Networks, phenotype labels, available cell types, and query thresholds differ between cohorts.",
        "meaning_cards": (
            card("Network structure", "Different edges change rankings", "Cohort-specific networks can place different genes near the same query program.", "blue"),
            card("Coverage", "Only 22 SEA-AD active calls", "Twenty of the 22 calls are male ε3/ε3, leaving most groups poorly covered.", "red"),
            card("Strongest agreement", "Two mitochondrial programs", "Female ε3/ε3 excitatory and male ε3/ε3 inhibitory patterns recur despite different drivers.", "green"),
        ),
        "meaning_bottom": "Program support can strengthen a ROSMAP finding without confirming its exact upstream candidate.",
        "not_proven": ("That zero exact matches refutes ROSMAP candidates", "Original contexts for LAGE3, MIPOL1, or PAPOLA", "A shared upstream cause for similar mitochondrial programs"),
        "next_tests": ("Freeze driver-associated signed gene sets before validation", "Harmonize networks, stable IDs, and thresholds", "Test matched and related contexts in a larger balanced cohort"),
        "literature": (
            literature("Female ε3/ε3 program", "Strong but narrow support", "Nine shared mtDNA genes are AD-up in both cohorts and overlap BH is 0.00505.", "Only one matched SEA-AD excitatory call was evaluable.", ""),
            literature("Male ε3/ε3 program", "Moderate to strong support", "Nineteen of 22 shared inhibitory-neuron genes have the same fixed direction.", "ROSMAP direct-broad significance is composition-sensitive.", ""),
            literature("Global driver overlap", "Suggestive, not significant", "Three cross-context genes exceed the random point expectation.", "The gene-level overlap P value is 0.0812.", ""),
        ),
    },
)


NEW_SLIDE_COUNT = len(FINDINGS) * SLIDES_PER_FINDING
OUTPUT_SLIDES = BASE_SLIDES + NEW_SLIDE_COUNT


def finding_slide_titles(finding: dict[str, Any]) -> tuple[str, ...]:
    number = finding["number"]
    return (
        f"FINDING {number}",
        finding["plain_title"],
        finding["evidence_title"],
        finding["context_title"],
        finding["meaning_title"],
        f"What Finding {number} does not prove, and the next evidence needed",
        f"Prior research and evidence context for Finding {number}",
    )


NEW_SLIDE_TITLES: tuple[str, ...] = tuple(
    title for finding in FINDINGS for title in finding_slide_titles(finding)
)


def finding_transitions(finding: dict[str, Any], next_number: int | None) -> tuple[str, ...]:
    closing = (
        f"Proceed to Finding {next_number}."
        if next_number is not None
        else "Close by returning to the strongest program-level results and the experiments needed to test causality."
    )
    return (
        "State the finding in plain language.",
        "Show the ROSMAP evidence behind the statement.",
        "Place the result in its cell-resolution and cross-cohort context.",
        "Explain why the result may matter biologically.",
        "Separate the observation from what remains unproven.",
        "Place the result in prior research and summarize its evidence level.",
        closing,
    )


NEW_SLIDE_TRANSITIONS: tuple[str, ...] = tuple(
    transition
    for index, finding in enumerate(FINDINGS)
    for transition in finding_transitions(
        finding,
        FINDINGS[index + 1]["number"] if index + 1 < len(FINDINGS) else None,
    )
)


TONE = {
    "blue": (ui.PALE_SKY, ui.BLUE),
    "green": (ui.PALE_GREEN, ui.TEAL),
    "gold": (ui.PALE_GOLD, ui.GOLD),
    "red": (ui.PALE_RED, ui.VERMILION),
    "gray": (ui.PALE_GRAY, ui.GRAY),
}


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


def visual_fingerprint(slide) -> tuple[Any, ...]:
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


def source_text(finding: dict[str, Any]) -> str:
    return f"Source: {ANALYSIS_SOURCE}, Finding {finding['number']}."


def notes_source(finding: dict[str, Any]) -> str:
    urls = [item["url"] for item in finding["literature"] if item["url"]]
    suffix = f" Literature: {'; '.join(urls)}" if urls else ""
    return f" Source: {ANALYSIS_SOURCE}, Finding {finding['number']}.{suffix}"


def add_three_cards(slide, cards: tuple[dict[str, str], ...], *, y: float = 1.62) -> None:
    for index, item in enumerate(cards):
        x = 0.72 + index * 4.15
        background, accent = TONE[item.get("tone", "blue")]
        ui.add_rect(slide, x, y, 3.78, 4.46, color=background, outline=None)
        ui.add_text(
            slide,
            item["label"].upper(),
            x + 0.30,
            y + 0.32,
            3.18,
            0.24,
            size=9.4,
            color=ui.readable_accent(accent),
            bold=True,
        )
        ui.add_text(
            slide,
            item["headline"],
            x + 0.30,
            y + 0.82,
            3.18,
            0.78,
            size=16.0 if len(item["headline"]) < 36 else 14.0,
            color=ui.NAVY,
            bold=True,
            align=PP_ALIGN.CENTER,
            valign=MSO_ANCHOR.MIDDLE,
            font=ui.FONT_HEAD,
        )
        ui.add_text(
            slide,
            item["body"],
            x + 0.34,
            y + 1.92,
            3.10,
            1.62,
            size=12.2,
            color=ui.DARK,
            align=PP_ALIGN.CENTER,
            valign=MSO_ANCHOR.MIDDLE,
        )


def build_divider(prs: Presentation, finding: dict[str, Any], transition: str):
    template = prs.slides[DIVIDER_TEMPLATE_INDEX]
    slide = ui.new_slide(prs, bg=ui.NAVY)
    for shape in template.shapes:
        slide.shapes._spTree.insert_element_before(
            copy.deepcopy(shape._element), "p:extLst"
        )
    replacements = {
        "TextBox 1": f"FINDING {finding['number']}",
        "TextBox 3": finding["title"],
        "TextBox 4": finding["kind"] + ".",
        "TextBox 6": "IN THIS FINDING",
        "TextBox 9": "Plain-language statement",
        "TextBox 12": "ROSMAP evidence",
        "TextBox 15": "Support and context",
        "TextBox 18": "Meaning, limits, literature",
        "TextBox 20": finding["divider_note"],
    }
    for shape_name, value in replacements.items():
        set_shape_text(slide, shape_name, value)
    title_shape = next(shape for shape in slide.shapes if shape.name == "TextBox 3")
    title_shape.text_frame.paragraphs[0].runs[0].font.size = Pt(
        20.0 if len(finding["title"]) >= 72 else 22.0
    )
    add_notes(
        slide,
        f"Introduce Finding {finding['number']}.",
        finding["divider_note"] + notes_source(finding),
        "This section presents a testable interpretation. KDA and transcript direction do not establish causal regulation or mitochondrial function.",
        transition,
    )
    return slide


def build_plain_slide(prs: Presentation, finding: dict[str, Any], transition: str):
    slide = ui.new_slide(prs)
    add_content_title(slide, finding["plain_title"], finding["plain_subtitle"])
    chip_colors = ((ui.PALE_SKY, ui.BLUE), (ui.PALE_GREEN, ui.TEAL), (ui.PALE_GOLD, ui.GOLD), (ui.PALE_RED, ui.VERMILION))
    for index, (text, colors) in enumerate(zip(finding["tags"], chip_colors, strict=True)):
        add_chip(slide, text, 0.82 + index * 3.08, 1.42, 2.78, bg=colors[0], accent=colors[1], size=10.4)
    add_three_cards(slide, finding["concepts"], y=2.16)
    ui.add_rect(slide, 0.72, 6.34, 11.90, 0.54, color=ui.WHITE, outline=ui.LIGHT)
    ui.add_text(slide, finding["plain_bottom"], 0.98, 6.48, 11.38, 0.26, size=11.4, color=ui.PURPLE, bold=True, align=PP_ALIGN.CENTER)
    add_source(slide, source_text(finding))
    add_notes(
        slide,
        f"Explain Finding {finding['number']} without assuming specialist knowledge.",
        finding["plain_subtitle"] + " " + finding["plain_bottom"] + notes_source(finding),
        "The slide explains the observed RNA or network pattern. It does not assign causality or functional consequence.",
        transition,
    )
    return slide


def row_colors(trend: str):
    if trend == "up":
        return ui.PALE_GREEN, ui.TEAL
    if trend == "down":
        return ui.PALE_RED, ui.VERMILION
    if trend == "mixed":
        return ui.PALE_GOLD, ui.GOLD
    return ui.PALE_SKY, ui.BLUE


def build_evidence_slide(prs: Presentation, finding: dict[str, Any], transition: str):
    slide = ui.new_slide(prs)
    add_content_title(slide, finding["evidence_title"], finding["evidence_subtitle"])
    metric_colors = ((ui.PALE_SKY, ui.BLUE), (ui.PALE_GREEN, ui.TEAL), (ui.PALE_GOLD, ui.GOLD))
    for index, ((value, label, detail), colors) in enumerate(zip(finding["metrics"], metric_colors, strict=True)):
        add_stat_card(slide, value, label, 0.72 + index * 4.15, 1.45, 3.78, bg=colors[0], accent=colors[1], detail=detail)
    for index, (label, value, detail, trend) in enumerate(finding["evidence_rows"]):
        y = 3.20 + index * 1.05
        background, accent = row_colors(trend)
        ui.add_rect(slide, 0.82, y, 11.70, 0.82, color=background, outline=None)
        ui.add_text(slide, label, 1.08, y + 0.18, 2.55, 0.32, size=13.0, color=ui.NAVY, bold=True)
        ui.add_text(slide, value, 3.74, y + 0.13, 2.16, 0.40, size=16.0, color=ui.readable_accent(accent), bold=True, align=PP_ALIGN.CENTER, font=ui.FONT_HEAD)
        ui.add_text(slide, detail, 6.12, y + 0.13, 5.98, 0.48, size=11.5, color=ui.DARK, valign=MSO_ANCHOR.MIDDLE)
    add_source(slide, source_text(finding))
    add_notes(
        slide,
        f"Present the primary ROSMAP evidence for Finding {finding['number']}.",
        "The three summary metrics and three evidence rows preserve the units used in the analysis. " + finding["evidence_subtitle"] + notes_source(finding),
        "Occurrences can repeat genes across fine-cell calls and are not independent donors. Exploratory aggregate scores are not final q-values unless stated otherwise.",
        transition,
    )
    return slide


def build_context_slide(prs: Presentation, finding: dict[str, Any], transition: str):
    slide = ui.new_slide(prs)
    add_content_title(slide, finding["context_title"], finding["context_subtitle"])
    add_three_cards(slide, finding["context_cards"], y=1.56)
    ui.add_rect(slide, 0.72, 6.30, 11.90, 0.58, color=ui.WHITE, outline=ui.LIGHT)
    ui.add_text(slide, finding["context_bottom"], 0.98, 6.44, 11.38, 0.30, size=11.3, color=ui.PURPLE, bold=True, align=PP_ALIGN.CENTER)
    add_source(slide, source_text(finding))
    add_notes(
        slide,
        f"Place Finding {finding['number']} in its internal and supplemental evidence context.",
        finding["context_subtitle"] + " " + finding["context_bottom"] + notes_source(finding),
        "Unavailable SEA-AD coverage is neutral. A tested gene not returned from a KDA call offers limited counterevidence because networks, labels, thresholds, and sample sizes differ.",
        transition,
    )
    return slide


def build_meaning_slide(prs: Presentation, finding: dict[str, Any], transition: str):
    slide = ui.new_slide(prs)
    add_content_title(slide, finding["meaning_title"], finding["meaning_subtitle"])
    add_three_cards(slide, finding["meaning_cards"], y=1.56)
    ui.add_rect(slide, 0.72, 6.30, 11.90, 0.58, color=ui.PALE_RED, outline=None)
    ui.add_text(slide, "Most cautious interpretation", 0.96, 6.45, 2.05, 0.26, size=9.6, color=ui.VERMILION_TEXT, bold=True)
    ui.add_text(slide, finding["meaning_bottom"], 3.05, 6.41, 9.10, 0.34, size=11.2, color=ui.DARK, bold=True, align=PP_ALIGN.CENTER)
    add_source(slide, source_text(finding))
    add_notes(
        slide,
        f"Explain why Finding {finding['number']} may matter without overstating function.",
        finding["meaning_subtitle"] + " " + finding["meaning_bottom"] + notes_source(finding),
        "Biological plausibility does not establish the direction of regulation, causality, or functional consequence.",
        transition,
    )
    return slide


def build_boundaries_slide(prs: Presentation, finding: dict[str, Any], transition: str):
    slide = ui.new_slide(prs)
    add_content_title(
        slide,
        f"What Finding {finding['number']} does not prove, and the next evidence needed",
        "The current analysis defines a testable hypothesis rather than a completed mechanism.",
    )
    ui.add_rect(slide, 0.72, 1.42, 5.78, 4.92, color=ui.PALE_RED, outline=None)
    ui.add_panel_title(slide, "Not proven", 1.04, 1.76, 5.10, accent=ui.VERMILION)
    ui.add_bullets(slide, list(finding["not_proven"]), 1.04, 2.38, 5.00, size=13.0, accent=ui.VERMILION, line_h=1.00)
    ui.add_rect(slide, 6.82, 1.42, 5.80, 4.92, color=ui.PALE_GREEN, outline=None)
    ui.add_panel_title(slide, "Best next tests", 7.14, 1.76, 5.12, accent=ui.TEAL)
    ui.add_bullets(slide, list(finding["next_tests"]), 7.14, 2.38, 5.02, size=13.0, accent=ui.TEAL, line_h=1.00)
    ui.add_text(slide, "Causal interpretation requires donor-aware statistics, perturbation, and functional measurement.", 0.92, 6.62, 11.50, 0.30, size=11.4, color=ui.PURPLE, bold=True, align=PP_ALIGN.CENTER)
    add_source(slide, source_text(finding))
    add_notes(
        slide,
        f"State the scientific boundaries and next experiments for Finding {finding['number']}.",
        "The left side lists claims that the current data cannot support. The right side lists experiments or analyses that directly address those gaps." + notes_source(finding),
        "Another expression dataset can improve reproducibility, but perturbation and functional rescue are needed for a causal mechanism.",
        transition,
    )
    return slide


def build_literature_slide(prs: Presentation, finding: dict[str, Any], transition: str):
    slide = ui.new_slide(prs)
    add_content_title(
        slide,
        f"Prior research and evidence context for Finding {finding['number']}",
        "Each source supports part of the interpretation. None independently proves the complete finding.",
    )
    backgrounds = ((ui.PALE_SKY, ui.BLUE), (ui.PALE_GREEN, ui.TEAL), (ui.PALE_GOLD, ui.GOLD))
    for index, (item, colors) in enumerate(zip(finding["literature"], backgrounds, strict=True)):
        x = 0.72 + index * 4.15
        ui.add_rect(slide, x, 1.48, 3.78, 4.74, color=colors[0], outline=None)
        ui.add_text(slide, item["citation"], x + 0.30, 1.80, 3.18, 0.42, size=15.0, color=ui.readable_accent(colors[1]), bold=True, align=PP_ALIGN.CENTER, font=ui.FONT_HEAD)
        ui.add_text(slide, item["topic"], x + 0.30, 2.36, 3.18, 0.58, size=13.5, color=ui.NAVY, bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
        ui.add_text(slide, "SUPPORTS", x + 0.32, 3.15, 1.10, 0.24, size=9.2, color=ui.readable_accent(colors[1]), bold=True)
        ui.add_text(slide, item["supports"], x + 0.32, 3.44, 3.14, 0.84, size=10.8, color=ui.DARK, align=PP_ALIGN.CENTER)
        ui.add_text(slide, "BOUNDARY", x + 0.32, 4.52, 1.10, 0.24, size=9.2, color=ui.GRAY, bold=True)
        ui.add_text(slide, item["boundary"], x + 0.32, 4.81, 3.14, 0.88, size=10.6, color=ui.GRAY, align=PP_ALIGN.CENTER)
    ui.add_rect(slide, 0.72, 6.38, 11.90, 0.50, color=ui.WHITE, outline=ui.LIGHT)
    ui.add_text(slide, f"Provisional novelty: {finding['novelty']}. Evidence strength and novelty are separate judgments.", 0.98, 6.51, 11.38, 0.26, size=10.8, color=ui.PURPLE, bold=True, align=PP_ALIGN.CENTER)
    add_source(slide, source_text(finding))
    add_notes(
        slide,
        f"Connect Finding {finding['number']} to prior research while preserving its novelty boundary.",
        "The slide distinguishes what each study or analysis supports from what it cannot establish." + notes_source(finding),
        "The novelty label is provisional and comes from a focused rather than systematic literature review.",
        transition,
    )
    return slide


def build_finding_slides(prs: Presentation, finding: dict[str, Any], transitions: tuple[str, ...]):
    return (
        build_divider(prs, finding, transitions[0]),
        build_plain_slide(prs, finding, transitions[1]),
        build_evidence_slide(prs, finding, transitions[2]),
        build_context_slide(prs, finding, transitions[3]),
        build_meaning_slide(prs, finding, transitions[4]),
        build_boundaries_slide(prs, finding, transitions[5]),
        build_literature_slide(prs, finding, transitions[6]),
    )


def update_transition(slide, transition: str) -> None:
    frame = slide.notes_slide.notes_text_frame
    if frame is None or "Transition:" not in frame.text:
        raise RuntimeError("Expected structured speaker notes on the preceding slide")
    frame.text = re.sub(r"Transition:.*$", f"Transition: {transition}", frame.text, flags=re.DOTALL)


def delete_tail(prs: Presentation, start_index: int) -> None:
    while len(prs.slides) > start_index:
        sld_id = prs.slides._sldIdLst[-1]
        prs.part.drop_rel(sld_id.rId)
        prs.slides._sldIdLst.remove(sld_id)


def validate(prs: Presentation, preserved_visuals: tuple[Any, ...]) -> None:
    if len(prs.slides) != OUTPUT_SLIDES:
        raise RuntimeError(f"Expected {OUTPUT_SLIDES} slides, found {len(prs.slides)}")
    observed = tuple(slide_title(prs.slides[BASE_SLIDES + index]) for index in range(NEW_SLIDE_COUNT))
    if observed != NEW_SLIDE_TITLES:
        mismatches = [
            f"{BASE_SLIDES + i + 1}: {actual!r} != {expected!r}"
            for i, (actual, expected) in enumerate(zip(observed, NEW_SLIDE_TITLES))
            if actual != expected
        ]
        raise RuntimeError("Unexpected finding slide titles: " + "; ".join(mismatches[:8]))
    if tuple(visual_fingerprint(prs.slides[index]) for index in range(BASE_SLIDES)) != preserved_visuals:
        raise RuntimeError("A visual element in the reviewed first 54 slides changed")
    for slide_number, slide in enumerate(prs.slides, start=1):
        notes = slide.notes_slide.notes_text_frame
        if notes is None or not all(label in notes.text for label in ("Teaching goal:", "Walk through:", "Scientific boundary:", "Transition:")):
            raise RuntimeError(f"Slide {slide_number} lacks structured speaker notes")
        for shape in slide.shapes:
            if (
                shape.left < 0
                or shape.top < 0
                or shape.left + shape.width > prs.slide_width + 10
                or shape.top + shape.height > prs.slide_height + 10
            ):
                raise RuntimeError(f"Out-of-bounds shape on slide {slide_number}: {shape.name}")


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    audit_root = args.audit_root.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)

    input_hash = sha256(input_path)
    prs = Presentation(input_path)
    titles = [slide_title(slide) for slide in prs.slides]
    if len(prs.slides) == BASE_SLIDES:
        action = "Appended"
    elif len(prs.slides) == OUTPUT_SLIDES and tuple(titles[BASE_SLIDES:]) == NEW_SLIDE_TITLES:
        delete_tail(prs, BASE_SLIDES)
        action = "Refreshed"
    else:
        raise RuntimeError(
            f"Unexpected deck state: {len(prs.slides)} slides; expected {BASE_SLIDES} "
            f"or a reviewed {OUTPUT_SLIDES}-slide all-findings deck"
        )

    preserved_visuals = tuple(visual_fingerprint(prs.slides[index]) for index in range(BASE_SLIDES))
    ui.set_notes_body_template(prs.slides[0].notes_slide.notes_placeholder._element)
    update_transition(prs.slides[BASE_SLIDES - 1], "Proceed to Finding 3, the coordinated female ε2 OXPHOS increase.")

    offset = 0
    for finding in FINDINGS:
        transitions = NEW_SLIDE_TRANSITIONS[offset : offset + SLIDES_PER_FINDING]
        build_finding_slides(prs, finding, transitions)
        offset += SLIDES_PER_FINDING

    validate(prs, preserved_visuals)
    audit_root.mkdir(parents=True, exist_ok=True)
    backup_dir = audit_root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"input_deck_{input_hash[:12]}.pptx"
    if not backup_path.exists():
        shutil.copy2(input_path, backup_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=output_path.stem + ".", suffix=".pptx", dir=output_path.parent)
    os.close(handle)
    temp_path = Path(temp_name)
    try:
        prs.save(temp_path)
        reopened = Presentation(temp_path)
        validate(reopened, preserved_visuals)
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    manifest_path = audit_root / "finding_slide_manifest.tsv"
    with manifest_path.open("w", encoding="utf-8") as handle_out:
        handle_out.write("slide_number\tfinding\tsection_title\n")
        for index, title in enumerate(NEW_SLIDE_TITLES, start=BASE_SLIDES + 1):
            finding_number = FINDINGS[(index - BASE_SLIDES - 1) // SLIDES_PER_FINDING]["number"]
            handle_out.write(f"{index}\t{finding_number}\t{title}\n")

    print(f"{action} Findings 3-17: {output_path}")
    print(f"Slides: {len(prs.slides)} ({NEW_SLIDE_COUNT} new)")
    print(f"Manifest: {manifest_path}")
    print(f"Backup: {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
