#!/usr/bin/env python3
"""Update only slide 62 speaker notes in the 2026-09-16 presentation."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


NOTES_PART = "ppt/notesSlides/notesSlide62.xml"

OLD_WALK_THROUGH = (
    "Walk through: Across included female APOE ε2 fine-cell comparisons, core MT genes "
    "contribute 128 DEG occurrences: 127 AD-up and one AD-down, so 99 percent are "
    "upregulated. Nuclear-encoded OXPHOS genes contribute 243 DEG occurrences: 239 AD-up "
    "and four AD-down, so 98 percent are upregulated. One occurrence means that one gene "
    "is a DEG in one fine-cell comparison; the same gene can contribute another occurrence "
    "in another comparison."
)

NEW_WALK_THROUGH = (
    "Walk through: This slide quantifies the female APOE epsilon-2 pattern. Across the "
    "included fine-cell comparisons, core MT genes contribute 128 DEG occurrences: 127 "
    "AD-up and one AD-down, so 99 percent are upregulated. Nuclear-encoded OXPHOS genes "
    "contribute 243 DEG occurrences: 239 AD-up and four AD-down, so 98 percent are "
    "upregulated. Both OXPHOS gene sets therefore show an almost uniform increase in AD."
)


def update_notes(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(source, "r") as src:
        names = src.namelist()
        if NOTES_PART not in names:
            raise RuntimeError(f"Missing expected notes part: {NOTES_PART}")

        notes_xml = src.read(NOTES_PART).decode("utf-8")
        if notes_xml.count(OLD_WALK_THROUGH) != 1:
            raise RuntimeError("Expected slide 62 walk-through paragraph exactly once")
        updated_notes = notes_xml.replace(OLD_WALK_THROUGH, NEW_WALK_THROUGH)

        with zipfile.ZipFile(destination, "w") as dst:
            for info in src.infolist():
                payload = (
                    updated_notes.encode("utf-8")
                    if info.filename == NOTES_PART
                    else src.read(info.filename)
                )
                dst.writestr(info, payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    update_notes(args.source, args.destination)


if __name__ == "__main__":
    main()
