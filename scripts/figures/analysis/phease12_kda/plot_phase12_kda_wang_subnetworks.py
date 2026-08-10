#!/usr/bin/env python3
"""Plot Wang-style directed KDA neighborhoods for APOE, LAMTOR5, and GABARAPL2."""

from __future__ import annotations

import argparse
from pathlib import Path

from phase12_kda_network_figure_common import DEFAULT_OUTPUT_DIR, generate_wang_subnetworks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--skip-hash-check", action="store_true")
    args = parser.parse_args()
    for path in generate_wang_subnetworks(args.output_dir, check_hashes=not args.skip_hash_check):
        print(path)


if __name__ == "__main__":
    main()
