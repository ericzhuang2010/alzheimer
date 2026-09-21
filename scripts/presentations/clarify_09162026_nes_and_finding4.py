#!/usr/bin/env python3
"""Define NES before first use and clarify the Finding 4 slides."""

from __future__ import annotations

import argparse
import html
import zipfile
from pathlib import Path


SLIDE_REPLACEMENTS: dict[int, dict[str, str]] = {
    15: {
        "Counts show whether each pathway had at least one significant result across the tested fine-cell contrasts and DEG lists.":
            "Direct broad-cell results use NES (normalized enrichment score). Positive = AD-up, negative = AD-down, and adjusted P < 0.05 = significant.",
    },
    67: {
        "Nuclear-sided decrease": "Nuclear-encoded OXPHOS decrease",
    },
    69: {
        "Direct broad-cell results do not reproduce the female ε4 nuclear decrease":
            "Direct broad-cell results do not reproduce the female ε4 fine-cell OXPHOS decrease",
        "Weak positive, not significant": "AD-up direction, not significant",
        "Significant positive direction":
            "Nuclear-encoded OXPHOS pathway is significantly AD-up",
        "Excitatory nuclear-encoded OXPHOS: normalized enrichment score (NES) = +0.70, adjusted P = 0.991.":
            "Excitatory neurons: NES = +0.70 and adjusted P = 0.991. The AD-up direction is not significant.",
        "Excitatory nuclear-encoded OXPHOS: normalized enrichment score (NES) = +2.01, adjusted P = 5.62 × 10⁻⁵.":
            "Excitatory neurons: NES = +2.01 and adjusted P = 5.62 × 10⁻⁵. The pathway result is significantly AD-up.",
        "Only two DEGs were shared with ROSMAP. Adjusted overlap P = 0.819.":
            "Only two DEGs overlapped with ROSMAP, and the overlap was not significant (adjusted P = 0.819).",
        "Describe this as a fine-cell female ε4 signal, not a broad-cell-wide effect.":
            "The female ε4 decrease is specific to the fine-cell analysis. Direct broad-cell results point upward.",
    },
    70: {
        "A nuclear-sided reduction could reflect lower respiratory investment, stress, or a shift in cell state.":
            "The decrease may reflect reduced expression of respiratory-complex genes, cellular stress, or a different cell state.",
        "Subtype composition or other aggregation effects may influence the fine-cell pattern.":
            "Differences in the mix of fine cell types may influence the direct broad-cell result.",
    },
    71: {
        "APOE4 and mitophagy": "APOE4 and mitochondrial quality control",
        "Links APOE4 models to mitochondrial dynamics and mitophagy.":
            "Links APOE4 models to mitochondrial dynamics and removal of damaged mitochondria.",
        "Connects APOE4 state to impaired mitochondrial homeostasis.":
            "Connects APOE4 state to impaired maintenance of mitochondrial function.",
    },
}


NOTES_REPLACEMENTS: dict[int, dict[str, str]] = {
    15: {
        "Teaching goal: Explain the two-stage pathway analysis and summarize how many pathways had at least one significant result.":
            "Teaching goal: Explain the fine-cell pathway analysis and define NES before the direct broad-cell results use it.",
        "Walk through: Each estimable fine-cell sex/APOE contrast was analyzed separately. For each contrast, the analysis created three mitochondrial DEG lists: all DEGs, genes upregulated in AD, and genes downregulated in AD. It then tested each pathway using the enrichment and significance definition on the previous slide. Twelve of the 46 Level 1 and Level 2 pathways and 18 of the 149 complete pathways had at least one significant result across the tested contrasts and DEG lists. Most significant results involved overlapping OXPHOS pathways. Non-OXPHOS signals were fewer and more localized. The next slide defines a separate descriptive overlap percentage used to summarize four recurring pathway sets across sex/APOE groups.":
            "Walk through: Each estimable fine-cell sex/APOE contrast was analyzed separately. For each contrast, the analysis created three mitochondrial DEG lists: all DEGs, genes upregulated in AD, and genes downregulated in AD. It then tested each pathway using the over-representation and significance definition on the previous slide. Twelve of the 46 Level 1 and Level 2 pathways and 18 of the 149 complete pathways had at least one significant result. Later direct broad-cell sensitivity analyses use a ranked-gene method and report a normalized enrichment score, or NES. Positive NES means that pathway genes rank toward higher expression in AD, and negative NES means that they rank toward lower expression in AD. An adjusted P value below 0.05 defines significance.",
        "Scientific boundary: The complete 149-pathway collection contains the 46 Level 1 and Level 2 pathways, so the two reported scopes overlap. At least one significant result means enrichment in at least one fine-cell, sex/APOE, and DEG direction list. It does not mean significance in every group or prove altered pathway activity.":
            "Scientific boundary: The complete 149-pathway collection contains the 46 Level 1 and Level 2 pathways, so the two reported scopes overlap. At least one significant result does not mean significance in every group. NES is a pathway-level ranking statistic, not a fold change, and it does not mean that every gene in the pathway changes significantly.",
    },
    67: {
        "Walk through: Nuclear-encoded OXPHOS genes provide the clear signal: 206 of 216 repeated DEG occurrences are lower in AD. Core MT genes are mixed, with 38 AD-down and 26 AD-up occurrences. Therefore the result is a nuclear-encoded OXPHOS decrease, not a uniform decrease across all MitoCarta MT genes.":
            "Walk through: Nuclear-encoded OXPHOS genes provide the clear signal: 206 of 216 repeated DEG occurrences are lower in AD. Core MT genes are mixed, with 38 AD-down and 26 AD-up occurrences. The result is therefore a decrease in nuclear-encoded OXPHOS gene expression rather than a uniform decrease across all MitoCarta MT genes.",
    },
    69: {
        "Walk through: The fine-cell DEG result points strongly downward for nuclear-encoded OXPHOS genes. The normalized enrichment score, or NES, summarizes the direction and strength of a pathway result; a positive NES indicates higher pathway expression in AD. In direct broad-cell analysis, the ROSMAP excitatory-neuron NES is weakly positive and not significant, while the SEA-AD excitatory-neuron NES is significantly positive. The available SEA-AD fine-cell check is only one small astrocyte DEG list and does not provide convincing support.":
            "Walk through: The fine-cell DEG result points strongly downward for nuclear-encoded OXPHOS genes. In direct broad-cell analysis, ROSMAP has an AD-up NES of +0.70, but its adjusted P value of 0.991 is not significant. SEA-AD has an AD-up NES of +2.01 with an adjusted P value of 5.62 × 10⁻⁵, so the pathway-level result is significant. This means that the pathway genes collectively rank toward higher expression in AD. It does not mean that every individual OXPHOS gene is significantly upregulated. The available SEA-AD fine-cell check contains only one small astrocyte DEG list, and its overlap with ROSMAP is not significant.",
        "Scientific boundary: The disagreement does not invalidate the fine-cell observation, but it prevents describing the decrease as a broad-cell-wide or cross-cohort effect. Aggregation, subtype composition, and limited matched coverage remain plausible explanations.":
            "Scientific boundary: The direct broad-cell pathway results point upward, opposite to the fine-cell DEG-occurrence pattern. This disagreement limits Finding 4 to the fine-cell analysis. Differences in the mix of fine cell types and limited matched coverage may contribute, but the current results do not identify the cause.",
    },
    70: {
        "Walk through: Most respiratory-complex subunits are encoded by nuclear DNA. Lower expression across many of these genes could reduce the supply of complex components or reflect a stress-associated cell state. APOE ε4 makes the hypothesis important because it strongly increases late-onset Alzheimer’s disease risk at the population level.":
            "Walk through: Most respiratory-complex subunits are encoded by nuclear DNA. Lower expression across many of these genes could reduce the supply of complex components, reflect cellular stress, or mark a different cell state. APOE ε4 makes the hypothesis important because it strongly increases late-onset Alzheimer’s disease risk at the population level.",
        "Scientific boundary: Gene expression alone cannot establish lower respiratory capacity, and the broad-cell direction reverses. The most cautious interpretation is a fine-cell signal that warrants targeted follow-up.":
            "Scientific boundary: Gene expression alone cannot establish lower respiratory capacity. The direct broad-cell pathway results point in the opposite direction, so the most cautious interpretation is a fine-cell signal that warrants targeted follow-up.",
    },
    71: {
        "Walk through: The cited APOE4 studies support the biological plausibility of altered mitochondrial homeostasis, and cell-resolved Alzheimer’s studies support strong heterogeneity among brain cell states. None reproduces the exact female APOE ε4 nuclear-encoded OXPHOS DEG pattern shown here.":
            "Walk through: The cited APOE4 studies support the biological plausibility of altered mitochondrial maintenance. This includes changes in mitochondrial dynamics and in the removal of damaged mitochondria. Cell-resolved Alzheimer’s studies also show that molecular responses differ among brain cell states. None reproduces the exact female APOE ε4 nuclear-encoded OXPHOS DEG pattern shown here.",
    },
}


def escaped(value: str) -> str:
    return html.escape(value, quote=False)


def apply_replacements(xml: str, replacements: dict[str, str], label: str) -> str:
    for old, new in replacements.items():
        old_xml = escaped(old)
        new_xml = escaped(new)
        if xml.count(old_xml) != 1:
            raise RuntimeError(f"{label}: expected one occurrence of {old!r}")
        xml = xml.replace(old_xml, new_xml)
    return xml


def update_deck(source: Path, destination: Path) -> None:
    updated: dict[str, bytes] = {}
    with zipfile.ZipFile(source, "r") as src:
        for slide, replacements in SLIDE_REPLACEMENTS.items():
            part = f"ppt/slides/slide{slide}.xml"
            xml = apply_replacements(src.read(part).decode("utf-8"), replacements, part)
            updated[part] = xml.encode("utf-8")

        for slide, replacements in NOTES_REPLACEMENTS.items():
            part = f"ppt/notesSlides/notesSlide{slide}.xml"
            xml = apply_replacements(src.read(part).decode("utf-8"), replacements, part)
            updated[part] = xml.encode("utf-8")

        with zipfile.ZipFile(destination, "w") as dst:
            for info in src.infolist():
                dst.writestr(info, updated.get(info.filename, src.read(info.filename)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    update_deck(args.source, args.destination)


if __name__ == "__main__":
    main()
