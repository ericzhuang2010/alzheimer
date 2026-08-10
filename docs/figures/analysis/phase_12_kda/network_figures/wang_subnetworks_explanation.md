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

## How the representative run in each panel was chosen

Exactly one prespecified, representative KDA run is displayed for each key
driver. The plotting code does not search all runs and select one dynamically;
the three run IDs are hard-coded in
[`phase12_kda_network_figure_common.py`](../../../../../../scripts/figures/analysis/phease12_kda/phase12_kda_network_figure_common.py),
following the choices recorded in
[`network_figure_creation_plan.md`](network_figure_creation_plan.md).

| Panel | Selected run | Selection rationale |
|---|---|---|
| A — `APOE` | Ast GRM3, male, APOE ε2, AD-down | A curated mechanistic example. Its five mitochondrial overlap genes include the two Complex V genes `ATP5PB` and `ATP5F1A`, and the run supplies the clearest connection to the earlier Ast GRM3 sex-direction reversal involving `TUFM`. It is **not** the APOE run with the smallest adjusted q-value: Ast DPP10 male-ε2 AD-down has a slightly smaller value (3.33 × 10⁻⁴ versus 4.11 × 10⁻⁴). |
| B — `LAMTOR5` | Exc L3/4 RORB CUX2, male, APOE ε2, AD-down | The statistically strongest primary directional `LAMTOR5` result by adjusted q-value (1.03 × 10⁻⁵). It has eight overlap genes, including the highlighted Complex V genes `ATP5IF1` and `ATP5MC2`. |
| C — `GABARAPL2` | Exc L4/5 RORB GABRG1, male, APOE ε2, AD-down | The statistically strongest primary directional `GABARAPL2` result by adjusted q-value (3.39 × 10⁻⁵). Its nine overlap genes include the mitochondrial stress or quality-control genes `CHCHD2`, `PARK7`, `BAX`, and `ATP5MC3`. |

All three selections follow several common constraints:

- They are **primary, directional** KDA runs, rather than secondary pooled
  analyses or the derived `AD_both_mito` union.
- The focal driver is significant and self-independent in the selected run.
- The run contains biologically informative mitochondrial targets.
- All panels use the male-ε2, AD-down setting, which improves cross-panel
  comparability.

Thus, panels B and C use the top statistical run for their respective drivers,
whereas panel A deliberately uses a representative run with a stronger
mechanistic interpretation. These panels should not be interpreted as showing
the only run supporting each driver. Cross-run recurrence must instead be
evaluated from the complete Phase 12 result tables and convergence summaries.

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

## How node size is scaled

The figure now uses a stronger node-size contrast based on each gene's total
degree in the complete broad-cell-type network.

The earlier version used a logarithmic area transform:

```text
area = 115 + 82 * log1p(total_degree)
```

That transformation compressed degree differences substantially, making the
largest and smallest nodes appear too similar.

Figure 6 of [Wang et al., *Cell*
2025](https://doi.org/10.1016/j.cell.2025.08.038) states that node and font
size are proportional to link degree and that KDP nodes are additionally
enlarged. However, neither the paper nor its
[released visualization-preparation
code](https://github.com/wange230/proteomics_networks/blob/main/codes/Baysian_network/generating_gephi_bn_nodes_edges.R)
reports the exact numeric size mapping.

The current figure therefore uses the following reproducible linear-diameter
rule:

```text
diameter_points = min(24, 7 + total_degree)
area_points_squared = diameter_points^2
```

The area conversion is necessary because NetworkX and Matplotlib accept node
marker area rather than diameter. Within this figure, degrees range from 1 to
16, producing node diameters from 8 to 23 points. Under the earlier logarithmic
area rule, the corresponding diameter range was only approximately 13 to 19
points. Low-degree nodes are therefore now noticeably smaller and hubs are
larger.

The key-driver diamonds receive an additional enlargement, following Wang's
subnetwork treatment. The 7-point baseline preserves the visibility of
low-degree nodes, while the 24-point cap prevents an extreme hub from
dominating the panel. Label font sizes remain fixed because degree-scaled fonts
would increase collisions in these compact, directly labeled subnetworks.

The node-size implementation is in
[`phase12_kda_network_figure_common.py`](../../../../../../scripts/figures/analysis/phease12_kda/phase12_kda_network_figure_common.py).
