#!/usr/bin/env python3
"""Revise slide 56 to describe the cross-cohort DEG comparison precisely."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


SLIDE_PART = "ppt/slides/slide56.xml"
NOTES_PART = "ppt/notesSlides/notesSlide56.xml"

REPLACEMENTS = {
    SLIDE_PART: {
        "8 matched KDA calls were evaluable. Support is gene-set-level rather than replication of the same gene returned from KDA calls.":
            "Eight eligible SEA-AD fine-cell DEG queries contributed. Support comes from shared MitoCarta MT DEGs and matching AD directions.",
        "shared MitoCarta MT query genes": "shared MitoCarta MT DEGs",
    },
    NOTES_PART: {
        "Teaching goal: Explain the matched SEA-AD support and what gene-set-level agreement means here.":
            "Teaching goal: Explain the matched SEA-AD DEG support and what cross-cohort directional agreement means here.",
        "Walk through: Eight matched male epsilon-3 homozygous inhibitory-neuron KDA calls were evaluable. ROSMAP and SEA-AD shared 22 mitochondrial-query genes, and 19 of the 22 had the same AD direction. Nine core MT genes were upregulated in both cohorts. Nuclear-encoded OXPHOS, protein-import, mitochondrial-ribosome, and maintenance genes were downregulated in both. The overlap was 22 genes compared with 15.17 expected and remained significant after correction, with a Benjamini-Hochberg adjusted P value of 0.0417. Excluding unresolved mitochondrial identity-conflict genes left 21 shared genes and a similar adjusted P value of 0.0486. Gene-set-level support means agreement among related input DEGs and their directions, not replication of the same gene returned from a KDA call.":
            "Walk through: Eight eligible SEA-AD male epsilon-3 homozygous inhibitory-neuron fine-cell DEG queries contributed to this comparison. ROSMAP and SEA-AD shared 22 MitoCarta MT DEGs, and 19 of the 22 had the same AD direction. Nine core MT genes were upregulated in both cohorts. Nuclear-encoded OXPHOS, protein-import, mitochondrial-ribosome, and maintenance genes were downregulated in both. The overlap was 22 genes compared with 15.17 expected and remained significant after correction, with a Benjamini-Hochberg adjusted P value of 0.0417. Excluding unresolved mitochondrial identity-conflict genes left 21 shared genes and a similar adjusted P value of 0.0486. The support therefore comes from shared DEGs and their directions across cohorts.",
        "Scientific boundary: This is focused cross-cohort support within the matched inhibitory-neuron context. It does not establish the same gene returned from KDA calls, protein-level imbalance, mitochondrial dysfunction, or a formal disease-by-sex-by-APOE interaction.":
            "Scientific boundary: This is focused cross-cohort DEG support within the matched inhibitory-neuron context. It does not establish protein-level imbalance, mitochondrial dysfunction, or a formal disease-by-sex-by-APOE interaction.",
    },
}


def revise(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(source, "r") as src, zipfile.ZipFile(destination, "w") as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename in REPLACEMENTS:
                text = data.decode("utf-8")
                for old, new in REPLACEMENTS[item.filename].items():
                    count = text.count(old)
                    if count != 1:
                        raise RuntimeError(
                            f"Expected one occurrence in {item.filename}, found {count}: {old!r}"
                        )
                    text = text.replace(old, new)
                data = text.encode("utf-8")
            dst.writestr(item, data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    revise(args.source, args.destination)


if __name__ == "__main__":
    main()
