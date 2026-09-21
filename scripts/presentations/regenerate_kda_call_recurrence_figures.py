#!/usr/bin/env python3
"""Regenerate recurrence heatmaps with audience-facing KDA-call terminology."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from update_sex_apoe_kda_combo_slides import (
    configure_plot_style,
    export_figure,
    plot_broad_cell_recurrence,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = (
    ROOT
    / "results/presentations/09162026_sex_apoe_kda_combo_update/figures"
)

FIGURES = {
    24: SOURCE_ROOT
    / "ros/ros_excitatory_driver_recurrence_matrix_plot_data.tsv",
    25: SOURCE_ROOT
    / "ros/ros_inhibitory_driver_recurrence_matrix_plot_data.tsv",
    26: SOURCE_ROOT
    / "ros/ros_astrocyte_driver_recurrence_matrix_plot_data.tsv",
    27: SOURCE_ROOT / "ros/ros_opc_driver_recurrence_matrix_plot_data.tsv",
    34: SOURCE_ROOT
    / "sea/sea_excitatory_driver_recurrence_matrix_plot_data.tsv",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    configure_plot_style()
    for slide_number, source_path in FIGURES.items():
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        plot_data = pd.read_csv(source_path, sep="\t")
        figure = plot_broad_cell_recurrence(plot_data)
        export_figure(
            figure,
            args.output_dir / f"slide-{slide_number}-recurrence",
        )
        plt.close(figure)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
