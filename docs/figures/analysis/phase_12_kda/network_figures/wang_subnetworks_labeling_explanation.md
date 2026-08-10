# Why only selected genes are labeled in the Wang-style subnetworks

The labels were intentionally curated to tell the figure's biological story
and avoid overcrowding. They were not automatically chosen by node size,
expression change, or statistical significance.

The labeling policy prioritizes:

- The focal key drivers: `APOE`, `LAMTOR5`, and `GABARAPL2`
- ATP-synthase/Complex V genes, such as `ATP5PB`, `ATP5F1A`, `ATP5IF1`,
  `ATP5MC2`, and `ATP5MC3`
- Genes in the KDA mitochondrial-signature overlap
- Intermediates on highlighted directed paths, such as `LDHB`, `POP7`,
  `MAGEF1`, and `SNAPC5`
- Selected mitochondrial or stress-related genes needed for the
  interpretation, such as `CHCHD10`, `PARK7`, `BAX`, and `MRPS18B`

The three panels contain 19, 27, and 45 nodes. Labeling every node—especially
all 45 in panel C—would make the figure unreadable. Therefore, all nodes and
edges remain visible, but only the prespecified genes receive text labels.

One important consequence is that an unlabeled node is not necessarily less
significant. For example, several unlabeled panel-C genes are still members of
the KDA overlap; their black rings communicate that status without text.

The exact label sets are manually defined in
[`phase12_kda_network_figure_common.py`](../../../../../../scripts/figures/analysis/phease12_kda/phase12_kda_network_figure_common.py),
and the rationale is documented in
[`network_figure_creation_plan.md`](network_figure_creation_plan.md#labels).

## Why some edges are highlighted

The dark edges highlight prespecified shortest directed paths from each key
driver to selected mitochondrial or ATP-synthase targets:

- Panel A:
  - `APOE → TUFM`
  - `APOE → ATP5PB`
  - `APOE → CHCHD10`
  - `APOE → LDHB → ATP5F1A`
- Panel B:
  - `LAMTOR5 → ATP5IF1`
  - `LAMTOR5 → POP7 → ATP5MC2`
- Panel C:
  - `GABARAPL2 → CHCHD2`
  - `GABARAPL2 → CHCHD2 → ATP5MC3`
  - `GABARAPL2 → MAGEF1 → SNAPC5 → PARK7`

They emphasize the biological routes central to the figure's narrative. The
pale edges are other directed connections in the reconstructed KDA
neighborhoods and remain as network context.

Importantly, a highlighted edge does **not** indicate greater confidence,
stronger regulation, or a larger effect. The production network has no
edge-confidence weights. When multiple equally short routes exist, the code
selects one reproducibly using alphabetical/lexicographic ordering.

The exact paths are recorded in
[`phase12_kda_wang_subnetworks_paths.tsv`](../../../../../../results/figures/analysis/phase12_kda/network_figures/phase12_kda_wang_subnetworks_paths.tsv).
