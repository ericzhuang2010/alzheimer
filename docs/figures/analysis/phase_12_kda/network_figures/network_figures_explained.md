# Phase 12 KDA network figures: outputs, captions, and interpretation

## Status

The four planned figures were generated from the validated Phase 12 KDA
production bundle. The production bundle itself was not modified. Before
plotting, the workflow verified its completion status, passed checks, recorded
input hashes, directed-acyclic-network structure, run-specific backgrounds,
selected neighborhood sizes, and the 26-gene ATP synthase / Complex V
definition.

Authoritative vector figures, presentation PNGs, auditable plotting tables,
and a checksum log are under:

`results/figures/analysis/phase12_kda/network_figures/`

## Shared visual language

- Arrows follow the Bayesian-network direction.
- A diamond identifies the KDA key driver.
- Node diameter increases linearly with full-network total degree, using
  `min(24, 7 + total_degree)` points. Degree is calculated in the complete
  broad-cell-type network, not in the displayed neighborhood. Key-driver
  diamonds receive an additional enlargement.
- Node fill is the matched Phase 08 AD-versus-NCI log fold-change: blue is
  lower in AD, orange is higher in AD, and white is unavailable.
- A black outer ring identifies a gene in that run's KDA overlap.
- A purple outer ring identifies a MitoCarta gene annotated as a Complex V
  subunit or assembly factor.
- Dark arrows mark prespecified shortest directed paths; pale arrows provide
  the remaining neighborhood context.

The full-network degree mapping is identical wherever marker size represents
connectivity: all nodes in Figures 1 and 2 and the driver nodes on the left of
Figure 3. Figure 3 target-node area instead represents supporting-call
recurrence, and Figure 4 point area represents significant-run recurrence;
those marks do not claim to encode network degree.

These encodings adapt the logic of Wang et al.'s multiscale network figure:
node size represents connectivity, node color represents differential
expression, and key-driver nodes receive a distinct visual treatment.

## Figure 1 — Wang-style driver neighborhoods

![Figure 1](../../../../results/figures/analysis/phase12_kda/network_figures/phase12_kda_wang_subnetworks.png)

Files:

- `phase12_kda_wang_subnetworks.pdf`, `.svg`, and `.png`
- `phase12_kda_wang_subnetworks_nodes.tsv`
- `phase12_kda_wang_subnetworks_edges.tsv`
- `phase12_kda_wang_subnetworks_paths.tsv`

### Main result

Three independently selected KDA neighborhoods connect cell-type-specific key
drivers with mitochondrial genes and ATP-synthase components:

- In male APOE-e2 `Ast GRM3`, the `APOE` neighborhood has 19 genes at layer 2,
  five overlap genes, fold enrichment 17.1, and adjusted P = 0.00041.
  Highlighted routes include `APOE → TUFM`, `APOE → ATP5PB`, and
  `APOE → LDHB → ATP5F1A`.
- In male APOE-e2 `Exc L3-4 RORB CUX2`, the `LAMTOR5` neighborhood has 27
  genes at layer 3, eight overlap genes, fold enrichment 14.0, and adjusted
  P = 1.0 × 10^-5. Highlighted routes include `LAMTOR5 → ATP5IF1` and
  `LAMTOR5 → POP7 → ATP5MC2`.
- In male APOE-e2 `Exc L4-5 RORB GABRG1`, the `GABARAPL2` neighborhood has 45
  genes at layer 3, nine overlap genes, fold enrichment 9.9, and adjusted
  P = 3.4 × 10^-5. Highlighted routes include `GABARAPL2 → CHCHD2`,
  `GABARAPL2 → MAGEF1 → SNAPC5 → PARK7`, and
  `GABARAPL2 → NDUFA4 → ATP5MC3`.

### Suggested caption

**Figure 1. Directed key-driver neighborhoods connect Phase 12 KDA signals to
mitochondrial and ATP-synthase genes.** Run-specific Bayesian-network
neighborhoods are shown for `APOE` in astrocytes and `LAMTOR5` and
`GABARAPL2` in excitatory neurons. Neighborhoods were reconstructed inside the
exact background tested by KDA and truncated at each result's selected layer.
Node fill represents matched AD-versus-NCI log fold-change, node area represents
full-network total degree, diamonds identify key drivers, black rings identify
KDA-overlap genes, and purple rings identify MitoCarta Complex V genes. Dark
arrows show prespecified shortest directed paths from each driver to selected
mitochondrial or ATP-synthase genes; pale arrows show other neighborhood edges.

### Slide message

The most direct answer to the professor's ATP question is that ATP-related
genes are present: `ATP5PB`, `ATP5F1A`, `ATP5IF1`, `ATP5MC2`, and `ATP5MC3`
appear within significant driver-centered neighborhoods. The selected systems
also connect them to mitochondrial translation and stress-response genes.

## Figure 2 — aligned female/male sex-reversal networks

![Figure 2](../../../../results/figures/analysis/phase12_kda/network_figures/phase12_kda_sex_reversal_networks.png)

Files:

- `phase12_kda_sex_reversal_networks.pdf`, `.svg`, and `.png`
- `phase12_kda_sex_reversal_networks_nodes.tsv`
- `phase12_kda_sex_reversal_networks_edges.tsv`
- `phase12_kda_sex_reversal_networks_paths.tsv`

### Main result

Each row uses one union topology and identical coordinates in both columns.
The left column shows the female APOE-e2 AD-up mitochondrial KDA result; the
right column shows the male APOE-e2 AD-down result. Nodes or edges absent from
a condition's reconstructed KDA neighborhood are faded.

The direction reversal is visible in the matched expression estimates:

| System | Gene | Female AD-up logFC | Male AD-down logFC |
|---|---:|---:|---:|
| Astrocyte `APOE` | `APOE` | +0.785 | -0.506 |
|  | `TUFM` | +0.506 | -0.939 |
|  | `ATP5PB` | +0.153 | -1.151 |
|  | `ATP5F1A` | +0.280 | -0.816 |
| Excitatory `LAMTOR5` | `LAMTOR5` | +0.505 | -0.928 |
|  | `ATP5IF1` | +0.420 | -0.497 |
|  | `ATP5MC2` | +0.492 | -0.560 |
| Excitatory `GABARAPL2` | `GABARAPL2` | +0.463 | -0.573 |
|  | `ATP5MC3` | +0.430 | -0.491 |
|  | `PARK7` | +0.532 | -0.442 |

The female `ATP5F1A` value is shown for topology comparison but was not a
paper-defined DEG and is not active in the female layer-1 `APOE` neighborhood;
the node and edge tables retain those distinctions explicitly.

### Suggested caption

**Figure 2. Shared driver-centered topology accompanies opposite female and
male mitochondrial expression directions in APOE-e2 strata.** Female AD-up
and male AD-down KDA neighborhoods are aligned for `APOE`, `LAMTOR5`, and
`GABARAPL2`. Coordinates are fixed within a row so differences in color,
overlap membership, and neighborhood inclusion can be compared directly.
Colors and node symbols follow Figure 1; faded elements are present in the
row's union graph but absent from the displayed condition's reconstructed
neighborhood.

### Slide message

The comparison is not only a change in KDA label. For the highlighted driver
and ATP-related genes, the matched log fold-changes are generally positive in
female APOE-e2 AD-up contexts and negative in male APOE-e2 AD-down contexts.

## Figure 3 — recurrent convergence on Complex V genes

![Figure 3](../../../../results/figures/analysis/phase12_kda/network_figures/phase12_kda_atp_convergence.png)

Files:

- `phase12_kda_atp_convergence.pdf`, `.svg`, and `.png`
- `phase12_kda_atp_convergence_complete.pdf`
- `phase12_kda_atp_convergence_pairs.tsv`
- focused and complete deterministic layout tables

### Main result

The focused map contains 27 driver–Complex V relationships. Edge width counts
distinct qualifying primary directional KDA calls after excluding mtDNA-encoded
drivers, self-overlap, overlap counts below two, and signatures smaller than ten
genes. Recurring relationships include:

- excitatory `GABARAPL2 → ATP5MC3`: 15 calls;
- excitatory `RPL11 → ATP5PF`: 14 calls;
- excitatory `LAMTOR5 → ATP5IF1`: 12 calls;
- excitatory `LAMTOR5 → ATP5MC2`: 12 calls;
- excitatory `RPL11 → ATP5ME`: 12 calls;
- inhibitory `RPS15 → ATP5F1E`: 6 calls;
- inhibitory `RPS15 → ATP5PF`: 6 calls;
- astrocyte `APOE → ATP5PB`: 2 calls.

The complete supplement contains all 93 qualifying broad-network,
driver, and Complex V target combinations.

### Suggested caption

**Figure 3. Primary directional KDA calls converge recurrently on ATP synthase
/ Complex V genes.** The bipartite map links selected key drivers to Complex V
genes found in their KDA overlaps. Driver color indicates the broad-cell-type
network. Driver size uses the same Wang-style linear-diameter mapping from
full-network total degree as Figures 1 and 2, including the common key-driver
enlargement. Target area indicates total supporting calls, edge width indicates
the number of qualifying KDA calls, and line style indicates directed
shortest-path distance. The main panel shows seven prespecified driver
families; the complete vector supplement shows all qualifying relationships.

### Slide message

The ATP finding is not confined to a single illustrative subnetwork. Several
driver–Complex V relationships recur across fine-cell-type, sex, and APOE
contexts, especially in excitatory and inhibitory neuronal networks.

## Figure 4 — connectivity versus aggregate KDA evidence

![Figure 4](../../../../results/figures/analysis/phase12_kda/network_figures/phase12_kda_connectivity_evidence.png)

Files:

- `phase12_kda_connectivity_evidence.pdf`, `.svg`, and `.png`
- `phase12_kda_connectivity_evidence_by_network.pdf`
- `phase12_kda_connectivity_evidence_points.tsv`
- `phase12_kda_connectivity_evidence_correlations.tsv`
- `phase12_kda_connectivity_evidence_labels.tsv`

### Main result

Across the 50,165 candidate-by-network records with ranking evidence,
within-network degree percentile is positively associated with
−log10(ACAT P) KDA evidence. The per-network Spearman correlations are:

| Broad network | Candidates | Spearman rho |
|---|---:|---:|
| Astrocytes | 7,547 | 0.523 |
| Excitatory neurons | 9,926 | 0.550 |
| Inhibitory neurons | 9,054 | 0.523 |
| Microglia | 5,547 | 0.360 |
| OPCs | 7,567 | 0.401 |
| Oligodendrocytes | 5,851 | 0.286 |
| Vasculature | 4,673 | 0.170 |

The association is strongest in excitatory neurons and weakest, though still
positive, in vasculature. The raw-degree faceted PDF is the diagnostic view;
the main panel uses within-network percentile so networks with different degree
distributions can be displayed together.

### Suggested caption

**Figure 4. Network connectivity provides contextual support for aggregate KDA
evidence.** Each point represents a candidate gene in one broad-cell-type
network. The x axis is full-network total-degree percentile within that network,
the y axis is −log10(ACAT P), point area is the number of significant primary directional KDA calls, and color denotes network. Panel B
reports the corresponding within-network Spearman correlation. Connectivity is
treated as supporting context rather than an independent significance test or
evidence of causality.

### Slide message

Highly connected genes tend to receive stronger aggregate KDA evidence, but
the strength of that relationship varies by network. This supports displaying
node connectivity while keeping KDA enrichment and recurrence as the primary
evidence.

## Interpretation boundaries

- A Bayesian-network arrow is a directed model edge, not proof that the source
  experimentally regulates the target.
- KDA significance is enrichment of a signature in a directed neighborhood;
  it is not a direct test of each displayed edge.
- Complex V membership is defined as the union of the Phase 03 MitoCarta
  `CV subunits` and `CV assembly factors` annotations. It is intentionally
  narrower than all genes with an `ATP5` prefix or all ATP-related biology.
- Figures 1 and 2 are selected mechanistic views. Figure 3 provides the
  conservative cross-run synthesis, and Figure 4 is a connectivity diagnostic.

## Reproduction

From the repository root:

```bash
python3 scripts/figures/analysis/phease12_kda/prepare_phase12_kda_network_figure_data.py
python3 scripts/figures/analysis/phease12_kda/plot_phase12_kda_wang_subnetworks.py
python3 scripts/figures/analysis/phease12_kda/plot_phase12_kda_sex_reversal_networks.py
python3 scripts/figures/analysis/phease12_kda/plot_phase12_kda_atp_convergence.py
python3 scripts/figures/analysis/phease12_kda/plot_phase12_kda_connectivity_evidence.py
python3 -m unittest tests/test_phase12_kda_network_figures.py -v
```

The scripts set a repository-local matplotlib cache, use deterministic layouts,
write figures atomically, and update
`phase12_kda_network_figures_generation_log.tsv` with SHA-256 hashes and UTC
timestamps.

## Validation summary

Ten automated tests pass, covering:

- the Phase 12 and figure-data checks;
- the fixed 26-gene Complex V annotation;
- prespecified driver–Complex V recurrence counts;
- exact Figure 1 neighborhood sizes and directed paths;
- identical coordinates within each Figure 2 pair; and
- existence and nonzero size of every planned PDF, SVG, and PNG;
- 300-dpi-scale PNG dimensions and auditable visual-encoding columns; and
- SHA-256 agreement between the generation log and every recorded artifact.
