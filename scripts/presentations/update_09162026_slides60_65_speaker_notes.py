#!/usr/bin/env python3
"""Refresh speaker notes for the revised Finding 3 slides 60 through 65."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


REPLACEMENTS: dict[int, dict[str, str]] = {
    60: {
        "Teaching goal: Introduce Finding 3 and distinguish it from the male APOE ε3/ε3 pattern.":
            "Teaching goal: Introduce Finding 3 and preview the evidence used to support it.",
        "Walk through: Finding 3 concerns female APOE ε2 cells. In the ROSMAP fine-cell analysis, core MT genes and nuclear-encoded OXPHOS genes were both predominantly upregulated in Alzheimer’s disease. The two OXPHOS gene sets therefore move together, unlike the opposite directions observed in male APOE ε3/ε3 cells. This section first states the result, then shows the occurrence counts, resolution checks, biological interpretation, and supporting literature.":
            "Walk through: Finding 3 concerns female APOE ε2 cells. In ROSMAP fine-cell comparisons of Alzheimer’s disease with no cognitive impairment, core MT genes and nuclear-encoded OXPHOS genes were both predominantly upregulated. This section begins with the direction of gene expression, then presents DEG-occurrence counts, compares fine-cell and direct broad-cell evidence, and ends with a cautious interpretation and literature context.",
        "Transition: State the female APOE ε2 result and define the two gene sets being compared.":
            "Transition: Define the two OXPHOS gene sets and show their direction in female APOE ε2 cells.",
    },
    61: {
        "Teaching goal: Explain the coordinated increase across the two OXPHOS gene sets.":
            "Teaching goal: Explain why both OXPHOS gene sets are described as upregulated together.",
        "Walk through: Core MT genes are the 13 protein-coding mitochondrial-DNA genes that encode structural OXPHOS subunits. Nuclear-encoded OXPHOS genes are the 86 nuclear genes that encode the remaining structural subunits used in this analysis. Across included female APOE ε2 fine-cell comparisons, 127 of 128 core MT gene occurrences and 239 of 243 nuclear-encoded OXPHOS gene occurrences were upregulated in AD. The result is therefore a coordinated RNA-level pattern across both gene sets.":
            "Walk through: Core MT genes are the 13 protein-coding genes in mitochondrial DNA that encode structural OXPHOS subunits. Nuclear-encoded OXPHOS genes are the 86 nuclear genes that encode the other structural subunits included in this analysis. Across the included female APOE ε2 fine-cell comparisons, 127 of 128 core MT gene occurrences and 239 of 243 nuclear-encoded OXPHOS gene occurrences were upregulated in AD. The two gene sets therefore show the same direction of gene-expression change.",
        "Scientific boundary: An occurrence is one gene identified as a DEG in one included fine-cell comparison, so the same gene may appear more than once across cell types. These counts do not measure unique genes, protein assembly, respiration, or ATP production.":
            "Scientific boundary: One occurrence means that one gene is a DEG in one included fine-cell comparison. The same gene can contribute another occurrence in another comparison. These counts do not measure unique genes, expression magnitude, protein assembly, respiration, or ATP production.",
        "Transition: Show the complete ROSMAP DEG-occurrence counts.":
            "Transition: Quantify the AD-up and AD-down occurrences for each gene set.",
    },
    63: {
        "Teaching goal: Explain how cell resolution and cohort coverage affect Finding 3.":
            "Teaching goal: Compare the fine-cell and direct broad-cell evidence for Finding 3.",
        "Walk through: The project treats fine-cell results as primary and direct broad-cell results as sensitivity evidence. In the fine-cell pathway analysis, nine of 12 excitatory fine cell types had significant enrichment of upregulated core MT genes and eight of 12 had significant enrichment of upregulated nuclear-encoded OXPHOS genes. In the direct broad-cell ROSMAP analysis, the nuclear-encoded OXPHOS increase remains strong, but the core MT component is not significant. SEA-AD has no matched female APOE ε2 fine-cell DEG result for this comparison.":
            "Walk through: Fine-cell ROSMAP supports both gene sets. Significant enrichment of upregulated genes appeared in nine of 12 fine cell types for core MT genes and eight of 12 for nuclear-encoded OXPHOS genes. Direct broad-cell ROSMAP supports the nuclear-encoded OXPHOS increase, but the core MT result was not significant. SEA-AD has no matched female APOE ε2 fine-cell DEG result, so it adds neither supporting nor contradictory evidence.",
        "Scientific boundary: The broad-cell disagreement limits how broadly the coordinated two-gene-set result can be generalized. Missing SEA-AD coverage is neutral: it provides neither validation nor contradictory evidence.":
            "Scientific boundary: The direct broad-cell result partially supports the finding but does not reproduce the coordinated two-gene-set pattern. The complete pattern is therefore supported mainly by fine-cell ROSMAP. Missing SEA-AD coverage is neutral.",
        "Transition: Explain why coordinated upregulation may be biologically interesting without calling it protective.":
            "Transition: Consider what coordinated upregulation might mean without assuming that it is protective.",
    },
    64: {
        "Teaching goal: Interpret the female APOE ε2 pattern cautiously.":
            "Teaching goal: Present the biological hypothesis while separating it from the evidence.",
        "Walk through: APOE ε2 lowers Alzheimer’s disease risk at the population level, but the current data come from diseased tissue. Both OXPHOS gene sets move upward rather than separating as they do in the male APOE ε3/ε3 finding. This coordinated response could reflect compensation for inefficient mitochondria or another altered disease state. It motivates a protective-response hypothesis for future testing.":
            "Walk through: APOE ε2 is associated with lower Alzheimer’s disease risk at the population level, but these data come from diseased tissue. Both OXPHOS gene sets are upregulated together. This pattern could reflect compensation for inefficient mitochondria or another disease-related state. It supports testing a protective-response hypothesis, but it does not establish one.",
        "Transition: Place the result in the context of APOE risk, mitochondrial biology, and sex-aware Alzheimer’s research.":
            "Transition: Review the prior research that supports parts of this interpretation.",
    },
    65: {
        "Teaching goal: Summarize the literature context and the novelty boundary for Finding 3.":
            "Teaching goal: Show which part of the interpretation each cited study supports.",
        "Walk through: Belloy and colleagues establish that Alzheimer’s disease risk differs substantially across APOE alleles, but that work does not explain this female APOE ε2 expression pattern. Lee and colleagues show that APOE state can alter mitochondrial homeostasis in another experimental context. Guo and colleagues support analyzing Alzheimer’s molecular networks by sex and cell type, but they do not report this exact female APOE ε2 OXPHOS result. The novelty label is therefore high but provisional.":
            "Walk through: Belloy and colleagues establish that Alzheimer’s disease risk differs across APOE alleles, but they do not explain this female APOE ε2 gene-expression pattern. Lee and colleagues show that APOE state can alter mitochondrial homeostasis in another experimental context. Guo and colleagues support sex-aware and cell-type-aware analysis of Alzheimer’s molecular networks, but they do not report this exact OXPHOS result. The novelty rating is therefore high but provisional.",
        "Transition: Move to Finding 4, which shows a different OXPHOS direction in female APOE ε4 fine-cell results.":
            "Transition: Move to Finding 4 and the different OXPHOS direction in female APOE ε4 cells.",
    },
}


def update_notes(source: Path, destination: Path) -> None:
    note_parts = {slide: f"ppt/notesSlides/notesSlide{slide}.xml" for slide in REPLACEMENTS}

    with zipfile.ZipFile(source, "r") as src:
        updated: dict[str, bytes] = {}
        for slide, replacements in REPLACEMENTS.items():
            part = note_parts[slide]
            xml = src.read(part).decode("utf-8")
            for old, new in replacements.items():
                if xml.count(old) != 1:
                    raise RuntimeError(
                        f"Slide {slide}: expected one occurrence of note paragraph: {old!r}"
                    )
                xml = xml.replace(old, new)
            updated[part] = xml.encode("utf-8")

        with zipfile.ZipFile(destination, "w") as dst:
            for info in src.infolist():
                dst.writestr(info, updated.get(info.filename, src.read(info.filename)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    update_notes(args.source, args.destination)


if __name__ == "__main__":
    main()
