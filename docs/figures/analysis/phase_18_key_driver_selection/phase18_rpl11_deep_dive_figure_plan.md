# Phase 18 RPL11 deep-dive figure plan

## Status

**Implemented and validated:** 2026-08-16

The analysis/table generator is
[`plot_phase18_rpl11_deep_dive.py`](../../../../scripts/figures/analysis/phase_18_key_driver_selection/plot_phase18_rpl11_deep_dive.py).
The standalone pathway network is rendered by Cytoscape through
[`render_phase18_rpl11_cytoscape.py`](../../../../scripts/figures/analysis/phase_18_key_driver_selection/render_phase18_rpl11_cytoscape.py).
The validated package is under
[`results/figures/analysis/phase_18_key_driver_selection/RPL11`](../../../../results/figures/analysis/phase_18_key_driver_selection/RPL11).

The former excitatory-neuron Panel A is exported as a standalone,
pathway-annotated consensus network. It removes the full-network locator,
includes all recorded RPL11-direct connections (0 incoming and 9 outgoing),
and sizes nodes by their occurrence in the 20 run-specific selected RPL11
neighborhoods. Its deeper mitochondrial hits retain the display-only threshold
of at least 4 of 20 supporting runs. Pathway markers use the local MSigDB C2:CP
v2026.1 collection and a custom background of genes in the full excitatory
Bayesian network, so no separate analysis phase or new raw data are required.

The unannotated exports named `phase18_rpl11_excitatory_consensus_network` were
deprecated and removed on 2026-08-16. The pathway-annotated version is the sole
standalone consensus-network figure.

On 2026-08-16, the former Matplotlib PNG/PDF/SVG pathway-network trio, the
first left-to-right Cytoscape version, and the first radial Cytoscape version
with guide rings and pathway dots were moved to `RPL11/archive`. The canonical
trio is now a collision-checked radial network without drawn guide rings,
exported directly by Cytoscape 3.10.4. Its editable `.cys` session,
visual-style XML, and machine-readable export log are stored beside the figure.

## Goal

Create an auditable RPL11 figure package that answers four questions:

1. Which mitochondrial-query genes lie downstream of RPL11 in the recorded
   excitatory-neuron and astrocyte Bayesian networks, and through which
   intermediate genes?
2. Which downstream mitochondrial genes recur across the Phase 18
   RPL11-supporting runs, fine cell types, sex/APOE groups, and query
   directions?
3. Is RPL11 more strongly associated with mitochondrial queries than
   comparable genes after accounting for network topology, expression and
   detection, and cytosolic-ribosomal annotation?
4. How much do the mitochondrial genes reached by RPL11 overlap among the
   AD-up and AD-down signatures/queries within each broad cell type?

The analysis is a mechanistic follow-up to the current Phase 18 selection. It
does not change the Phase 18 top-five lists.

## Required output directory

All generated figures, tables, graph files, captions, methods, checks, and
manifests must be written under:

```text
results/figures/analysis/phase_18_key_driver_selection/RPL11
```

The implementation must create this directory if it does not exist and replace
only files declared as part of the RPL11 package.

## Scope

### Primary networks

The main directed-network panels will use:

- `Excitatory_neurons`
- `Astrocytes`

These are the most informative RPL11 contexts for network interpretation:

| Network | Eligible / usable runs | Conservative-support runs | Aggregate ACAT q | Stability candidate retention |
|---|---:|---:|---:|---:|
| Excitatory neurons | 97 / 97 | 20 | 1.8402 × 10^-9 | 14/14 |
| Astrocytes | 21 / 20 | 3 | 3.4404 × 10^-5 | 2/3 |

RPL11 also passes in microglial and oligodendrocyte networks, but each has only
one conservative-support run. Those results should be noted in the caption or
summary table, not drawn as equally supported mechanistic network panels.
They should nevertheless be included in the query-overlap summary so all broad
networks in which RPL11 is selected are accounted for.

### Direction convention

For an input edge:

```text
A → B
```

`A` is treated as upstream and `B` as downstream. The KDA neighborhood is
cumulative:

```text
layer 1 = RPL11 plus direct downstream neighbors
layer 2 = layer 1 plus one additional downstream step
layer 3 = layer 2 plus one additional downstream step
```

The driver is part of the stored neighborhood size. Because RPL11 is a non-MT
driver, it is not a member of the mitochondrial query and does not contribute
to query overlap.

For the centered network visualization, upstream and downstream context must
be distinguished explicitly:

```text
upstream depth 1 = nodes with an edge into RPL11
upstream depth 2 = nodes that reach RPL11 in two directed steps
downstream depth 1-3 = the KDA layers defined above
```

Upstream nodes provide regulatory context only. They were not included in the
downstream KDA enrichment calculation and must never be counted as query hits.
The main display will show up to two upstream layers and up to three downstream
layers. All three upstream layers will still be audited in the exported data.

Bayesian-network directions are model-derived hypotheses. An arrow must not be
described as experimental proof that RPL11 directly regulates the target.

## Inputs

### Current Phase 18 result

- [`call_key_driver_returns.tsv`](../../../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv)
- [Non-MT evidence-atlas gene summary](../../../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt_gene_summary.tsv)
- [Non-MT evidence-atlas gene-network details](../../../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt_gene_network_details.tsv)

The canonical return table supplies the current aggregate decisions,
run-specific final layers, conservative-support flags, ranks, stability
summaries, and sex/APOE/query-direction identities.

### Recorded Bayesian networks

- [`Excitatory_neurons/result.links3.links.txt`](../../../../data/bayesian_network/Excitatory_neurons/result.links3.links.txt)
- [`Astrocytes/result.links3.links.txt`](../../../../data/bayesian_network/Astrocytes/result.links3.links.txt)

The first column is the source and the second column is the target.

### Run query and background membership

- [`kda_run_manifest.tsv`](../../../../results/minerva_production/12_kda/kda_run_manifest.tsv)
- [`kda_signature_members.tsv.gz`](../../../../results/minerva_production/12_kda/kda_signature_members.tsv.gz)
- [`kda_background_members.tsv.gz`](../../../../results/minerva_production/12_kda/kda_background_members.tsv.gz)

These are upstream run inputs already used to reconstruct the current Phase 18
table. They are needed because a run-specific induced network contains only
genes in that run's tested background. No deprecated Phase 12 selected-gene
list, ranking, analysis figure, or biological conclusion will be used.

### Gene annotation and expression/detection matching

- [`gene_annotation_master.tsv.gz`](../../../../results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz)
- Phase 5 normalization manifests under
  [`results/minerva_production/05_normalized`](../../../../results/minerva_production/05_normalized)

The Phase 9 table supplies MitoCarta membership, HGNC names, raw-count totals,
and detected-nucleus counts. The Phase 5 manifests supply the total number of
nuclei for each assay object. These fields allow disease-label-independent
matching on:

```text
log1p(total raw counts / total nuclei)
nuclei detected / total nuclei
```

For excitatory neurons, count and detection summaries must be combined across
the three excitatory assay sets using totals, not an unweighted mean. The
large normalized RDS objects are not required for the initial figure package.

### Earlier direct-DEG annotation

The Phase 8 MAST output files may be used only to annotate whether a displayed
node met the stored `paper_deg` rule and in which directions. DEG evidence does
not determine which nodes enter the graph.

### Visual design reference

- [Wang et al. multiscale-modeling paper, Figure 6](../../../related_papers/wang_multiscale_modeling.pdf)

The plan should borrow Figure 6's useful visual grammar: a faint global-network
locator, an enlarged central key driver, degree-scaled nodes and labels,
directed arrows, and node color for expression direction. It should not copy
the figure literally. Phase 18 contains several DEG contrasts, so mixed or
discordant directions must be shown explicitly rather than collapsed into a
single red/blue value.

## Fixed current-data anchors

The implementation must reproduce these values before rendering.

### Full-network topology

| Quantity | Astrocytes | Excitatory neurons |
|---|---:|---:|
| Full network nodes | 8,285 | 10,441 |
| Full network edges | 8,881 | 13,759 |
| RPL11 in-degree | 1 | 0 |
| RPL11 out-degree | 3 | 9 |
| RPL11 total undirected degree | 4 | 9 |
| Upstream genes at exact depth 1 | 1 (`RPLP1`) | 0 |
| Upstream genes at exact depth 2 | 1 (`RPS25`) | 0 |
| Downstream genes through layer 3, excluding RPL11 | 106 | 114 |
| Core MitoCarta genes downstream through layer 3 | 22 | 25 |

Astrocyte direct topology:

```text
RPLP1 → RPL11 → COX7C
                 CWC15
                 PRDX1
```

Excitatory direct downstream neighbors:

```text
COX7C, SMDT1, RPL30, RPL5, RPL6, RPS13, RPS23, RPS27A, SRP14
```

### Supporting-run layer distribution

| Network | Layer 1 | Layer 2 | Layer 3 |
|---|---:|---:|---:|
| Astrocytes | 0 | 2 | 1 |
| Excitatory neurons | 0 | 1 | 19 |

The dominance of layer 3 in excitatory neurons must be stated in the figure or
caption. Most excitatory evidence is a multi-step downstream-module result,
not a direct-edge result.

### Recurrent mitochondrial-query hits

Astrocyte supporting runs: `n = 3`.

| Gene | Supporting runs containing the hit |
|---|---:|
| COX7C | 3/3 |
| PSAP | 3/3 |
| TOMM7 | 2/3 |
| NDUFB4 | 2/3 |
| UQCRB | 2/3 |
| ATP5PF | 2/3 |

Excitatory supporting runs: `n = 20`.

| Gene | Supporting runs containing the hit |
|---|---:|
| COX7C | 19/20 |
| UQCRQ | 16/20 |
| NDUFS5 | 16/20 |
| NDUFA1 | 15/20 |
| RPL13 | 14/20 |
| NDUFB9 | 13/20 |
| ATP5PF | 13/20 |
| ATP5ME | 12/20 |
| NDUFB3 | 12/20 |
| SLC25A5 | 11/20 |

These frequencies mean that a gene was both in the run's mitochondrial query
and in the selected RPL11 downstream neighborhood. They do not mean that the
gene was differentially expressed in every Phase 8 contrast.

### Direction-group query-overlap anchors

For this figure, a **supporting query** is one conservative-support RPL11 run,
identified by broad network, fine cell type, sex/APOE group, and AD-up or
AD-down mitochondrial direction. Within each broad network, the two Venn sets
are the unions of RPL11 query-hit genes across the supporting AD-up queries and
supporting AD-down queries, respectively.

| Broad network | Supporting AD-up / AD-down queries | AD-up union | Shared | AD-down union | AD-up only / AD-down only |
|---|---:|---:|---:|---:|---:|
| Excitatory neurons | 7 / 13 | 21 | 20 | 24 | 1 / 4 |
| Astrocytes | 1 / 2 | 6 | 6 | 12 | 0 / 6 |

The excitatory AD-up-only gene is `COX20`; the AD-down-only genes are `APOO`,
`MRPS18C`, `RPS12`, and `TXNRD1`. All six astrocyte AD-up genes also occur in
the AD-down union; its AD-down-only genes are `ATP5F1E`, `ATP5ME`, `COX6C`,
`CYB5R3`, `SLIRP`, and `UQCRH`.

Microglia and oligodendrocytes each have one conservative-support AD-down query
and no supporting AD-up query. They therefore receive a labeled one-set summary,
not an artificial two-set overlap. The microglial set contains 5 hits
(`FTH1`, `APOO`, `TXNRD1`, `ATP5F1E`, `UQCRB`); the oligodendrocyte set contains
4 (`TXNRD1`, `RPL13`, `FTH1`, `ATP5MC2`).

## Analysis steps

### Step 1 — validate and load the graphs

Load each full network as a `networkx.DiGraph`. Check for empty symbols,
self-edges, duplicated edges, and the fixed node/edge counts above. Confirm
that RPL11 occurs exactly once as a node.

Save a complete full-network topology summary. Do not modify or reorient input
edges.

### Step 2 — reconstruct full directed RPL11 neighborhoods

For each network, calculate:

- immediate upstream neighbors;
- exact upstream distance 1, 2, and 3 in the reversed graph;
- exact downstream distance 1, 2, and 3;
- cumulative layer-1, layer-2, and layer-3 neighborhoods;
- all shortest directed paths of length at most 3 from RPL11 to a
  mitochondrial-query hit; and
- in-degree, out-degree, total degree, and path multiplicity for displayed
  nodes.

The calculation must match the cumulative layer convention used by
`scripts/18_export_significant_returns.py`.

### Step 3 — reconstruct the supporting run-specific induced graphs

For every included RPL11 row in the two primary networks:

1. obtain the run's effective query and background;
2. induce the broad Bayesian network on that background;
3. reconstruct RPL11 layers 1–3;
4. confirm the stored `final_layer`, overlap count, neighborhood size, fold
   enrichment, raw P, and run q; and
5. for conservative-support runs, record every query-overlap gene and the
   minimum directed distance from RPL11.

Generation must stop if the reconstructed values disagree with the canonical
Phase 18 table beyond numerical tolerance.

### Step 4 — create the reduced network-display subgraphs

A complete three-layer graph is too dense for the main figure. Construct a
reduced display graph separately for each network.

Include:

1. RPL11;
2. all upstream nodes within two directed steps of RPL11, drawn in a separate
   visual sector and explicitly marked as not part of KDA enrichment;
3. every mitochondrial-query hit meeting the recurrence rule below; and
4. all nodes and edges on shortest directed paths of length at most 3 from
   RPL11 to those retained hits.

Recurrence rule:

```text
Astrocytes: retain hits present in at least 2 of 3 supporting runs
Excitatory neurons: retain hits present in at least 4 of 20 supporting runs
```

The excitatory threshold is 20% and is intended only to control display
density. It is not a new scientific-significance threshold. A supplementary
GraphML and TSV package must retain the complete three-layer RPL11 graph.

If multiple shortest paths reach a retained hit, keep all shortest paths so
the figure does not invent a unique mechanism.

Render each reduced graph as an RPL11-centered causal subnetwork inspired by
Wang et al. Figure 6. Place upstream nodes to the left or upper-left with arrows
pointing toward RPL11, and downstream nodes to the right or radially outward
with arrows pointing away from RPL11. The excitatory panel must explicitly say
`no recorded upstream parents` because RPL11 has in-degree zero there; do not
add inferred or external upstream regulators.

Add a small locator inset for each broad network: draw the full network in
very light gray, mark RPL11, and highlight the displayed local subgraph. The
locator is contextual and should not carry gene labels. If the full-network
overview becomes an unreadable dark mass at final size, show only its weakly
connected-component hull or density raster plus the highlighted local nodes.

### Step 5 — annotate nodes and edges

Each node table must include:

- `network`
- `gene`
- `minimum_upstream_depth`
- `minimum_downstream_depth`
- `network_role` (`upstream`, `driver`, `downstream`)
- `is_rpl11`
- `is_upstream_context`
- `is_core_mitocarta`
- `is_cytosolic_ribosomal`
- `is_required_intermediate`
- `supporting_run_count`
- `supporting_run_fraction`
- `supporting_fine_cell_type_count`
- `supporting_groups`
- `supporting_directions`
- `phase08_paper_deg_any`
- `phase08_up_count`
- `phase08_down_count`
- `in_degree_full`
- `out_degree_full`
- `shortest_path_count_from_rpl11`

Cytosolic-ribosomal annotation should use the HGNC name beginning with
`ribosomal protein` while excluding names containing `mitochondrial`. Do not
use an unrestricted `RPL*` or `RPS*` prefix alone because that would
misclassify genes such as ribosomal-S6 kinases.

Each edge table must include source, target, network, source/target upstream
and downstream depths, whether the edge is on a retained shortest path, and
whether it is an upstream-context edge.

### Step 6 — build the run-by-target support matrix

Rows are mitochondrial-query hits observed in at least one conservative RPL11
supporting run. Columns are the 23 conservative-supporting runs: 20 excitatory
and 3 astrocyte.

Each cell records:

```text
0 = not a query hit in the selected RPL11 neighborhood
1 = first reached at directed depth 1
2 = first reached at directed depth 2
3 = first reached at directed depth 3
```

Column annotations must show:

- broad network;
- fine cell type;
- sex/APOE group;
- AD-up or AD-down mitochondrial query;
- stored selected RPL11 layer;
- other-query overlap;
- fold enrichment; and
- final run q.

Rows should be grouped by mitochondrial function when a recorded annotation
is available, but functional grouping must not change row inclusion.

### Step 7 — summarize overlap among RPL11-supporting queries

Build a long table with one row per:

```text
broad network × supporting query × RPL11 query-hit gene
```

The query identifier must retain fine cell type, sex/APOE group, query
direction, final layer, and run q. From this table:

1. make a two-set Venn diagram for excitatory neurons and astrocytes, comparing
   the union of AD-up hits with the union of AD-down hits;
2. show a one-set summary for microglia and oligodendrocytes, which each have
   only one supporting AD-down query;
3. label every Venn region with its exact unique-gene count and report the
   number of contributing supporting queries beside each set name; and
4. retain the run-by-target matrix, or an UpSet-style supplement, for exact
   individual-query overlap.

A classical Venn diagram must not be drawn with 20 individual excitatory query
sets. The direction-level Venn answers whether RPL11 reaches shared versus
direction-specific mitochondrial genes. The matrix/UpSet view answers which
individual fine-cell-type × sex/APOE queries contain each hit.

Validate the fixed union and intersection counts above. Export the exact genes
in each Venn region; the circles alone are not an analysis record.

### Step 8 — run matched-control specificity analyses

The candidate universe is all assessable `non_mt_driver` genes in the same
broad network with:

```text
coverage_fraction >= 0.80
nonmissing aggregate_acat_p
gene != RPL11
```

Use three prespecified control analyses.

#### Null A — topology matched

Match on:

- out-degree;
- total undirected degree;
- cumulative downstream-neighborhood size at layers 1, 2, and 3; and
- coverage fraction.

This asks whether any similarly connected non-MT gene produces equally strong
cross-run mitochondrial enrichment.

#### Null B — topology plus expression/detection matched

Add:

- `log1p(total raw counts / total nuclei)`; and
- detected-nucleus fraction.

This asks whether RPL11's result is explained by being abundant and broadly
detected.

#### Null C — cytosolic-ribosomal matched

Restrict the control universe to other cytosolic ribosomal proteins and apply
the topology plus expression/detection matching. This asks whether RPL11 is
exceptional within its own biological class.

For each null:

1. robust-standardize the matching features within network using median and
   median absolute deviation;
2. calculate deterministic Euclidean matching distance;
3. retain the nearest controls up to 250, while reporting the complete
   distance and feature-balance table;
4. repeat the comparison using fixed calipers as a sensitivity analysis; and
5. never duplicate a control gene to create an artificially large null.

Fixed sensitivity calipers are:

```text
absolute out-degree difference <= 1
absolute total-degree difference <= 2
absolute log1p(layer-3 neighborhood size) difference <= 0.25
absolute expression robust-z difference <= 0.5
absolute detected-fraction difference <= 0.10
```

For Null A, ignore the expression and detection calipers. For Null C, require
cytosolic-ribosomal status exactly. If fewer than 20 controls satisfy a null,
show every control point, report `n`, and describe the result as descriptive
rather than assigning a precise empirical P value.

Compare RPL11 with the controls using:

- `-log10(aggregate_acat_p)`;
- conservative-support run count;
- supporting fine-cell-type count; and
- leave-one-fine-cell-type candidate-retention fraction where assessable.

The empirical tail P is:

```text
(1 + number of unique matched controls at least as extreme as RPL11)
--------------------------------------------------------------------
                    (1 + number of unique controls)
```

The current archived degree-only sensitivity result may be shown as historical
context but must not substitute for this analysis. It used 100 nearest-degree
draws and gave the minimum possible value, 1/101 = 0.0099, for both networks.
It did not match expression, detection, neighborhood size at all layers, or
ribosomal status, and it was not a Phase 18 selection gate.

### Step 9 — compare RPL11 with other selected ribosomal drivers

As a supplementary analysis, compare RPL11 with:

```text
RPLP1, RPL15, RPS13, RPS15, RPL38
```

Within each applicable broad network, calculate:

- Jaccard overlap of complete three-layer downstream neighborhoods;
- Jaccard overlap of mitochondrial-query hits;
- recurrent hits unique to each driver;
- shared shortest-path intermediates; and
- matched-null percentile.

This analysis determines whether RPL11 has a distinctive mitochondrial module
or represents a broader ribosomal-network signal.

## Figure package

### Figure 1 — RPL11 directed-network evidence

Base filename:

```text
phase18_rpl11_deep_dive
```

Implemented layout: 12 × 9 inches, four panels. Panels A and B use the
centered causal-subnetwork style of Wang et al. Figure 6, adapted to show both
recorded upstream context and the downstream KDA neighborhood.

#### Panel A — excitatory-neuron directed neighborhood

- Enlarge and center RPL11; place its depth-1 to depth-3 downstream paths
  radially outward or left-to-right while preserving arrow direction.
- Include a faint, unlabeled full-network locator inset with RPL11 and the
  extracted local subgraph highlighted.
- Display recurrent mitochondrial hits and every shortest-path intermediate.
- State `no recorded upstream parents` in the panel.
- Add a compact evidence strip with `20/97` conservative support, aggregate q,
  and `14/14` stability retention.
- State `19 of 20 supporting runs selected layer 3` directly in the panel.

#### Panel B — astrocyte directed neighborhood

- Use the same centered visual grammar as Panel A.
- Show the recorded upstream chain `RPS25 → RPLP1 → RPL11` in the upstream
  sector, visually separated from the downstream KDA neighborhood.
- Include a faint, unlabeled full-network locator inset.
- Add `3/20` conservative support, aggregate q, and `2/3` stability retention.

#### Panel C — supporting run-by-target matrix

- Rows: observed mitochondrial-query hits.
- Columns: 23 conservative-supporting runs.
- Cell fill: first directed depth 1–3, using a discrete colorblind-safe
  sequential palette.
- Empty cells remain white and contain no zero-like color.
- Group columns first by network, then direction, sex/APOE group, and fine cell
  type using a fixed deterministic order.

#### Panel D — matched-control specificity

- Facet by network and null model.
- Show every matched control as a point or empirical cumulative distribution.
- Draw RPL11 as a labeled black diamond/vertical line.
- Primary x-axis: `-log10(aggregate ACAT P)`.
- Add compact secondary summaries for conservative-support and fine-cell-type
  counts if space permits; otherwise place them in Figure 2.
- Print control `n`, empirical tail P, and matching-balance status.

### Figure 2 — ribosomal-driver comparison

Base filename:

```text
phase18_rpl11_ribosomal_comparison
```

This is a supplementary figure containing:

- pairwise Jaccard heatmap for complete three-layer neighborhoods;
- pairwise Jaccard heatmap for mitochondrial-query hits;
- UpSet-style membership plot for recurrent mitochondrial hits; and
- topology/expression/matched-null summary for each ribosomal driver.

If the comparison is too sparse to support a readable UpSet plot, replace it
with a directly labeled driver-by-target presence matrix. Do not use a Venn
diagram for more than three sets.

### Figure 3 — overlap among RPL11-supporting queries

Base filename:

```text
phase18_rpl11_query_overlap
```

Implemented layout: 10.5 × 7.2 inches, four panels.

- **Panel A:** excitatory-neuron AD-up versus AD-down Venn. Subtitle:
  `7 AD-up queries; 13 AD-down queries`. Regions must reproduce 1 up-only,
  20 shared, and 4 down-only mitochondrial hit genes.
- **Panel B:** astrocyte AD-up versus AD-down Venn. Subtitle:
  `1 AD-up query; 2 AD-down queries`. Regions must reproduce 0 up-only,
  6 shared, and 6 down-only genes.
- **Panel C:** exact query-overlap matrix or UpSet-style view for the 20
  excitatory supporting queries, annotated by fine cell type, sex/APOE group,
  and direction.
- **Panel D:** compact exact-query view for astrocytes plus one-set summaries
  for the single microglial and oligodendrocyte supporting queries.

The Venn-set elements are unique RPL11 query-hit genes, not runs. The set
labels show both the union gene count and the number of supporting queries used
to construct that union. If circles are not area-proportional, state this in
the caption. Exact genes and memberships are provided in the companion TSV.

### Standalone pathway-annotated excitatory consensus network

Base filename:

```text
phase18_rpl11_excitatory_consensus_network_pathways
```

This figure uses 35 circular nodes, 34 edges, recurrence sizes, DEG fills, and
mitochondrial-hit borders; no ribosome-specific square shape is used. RPL11 is
centered; D1, D2, and D3 nodes lie at
progressively larger radial distances, but the three guide circles are not
drawn. Nodes within each depth are equally spaced, deeper circles are rotated
toward their parent nodes, and a pairwise clearance check prevents overlap.
The compact radii (270, 460, and 650 Cytoscape units) shorten the arrows while
label-aware node diameters of 112–156 units support 19–25-point labels. Colored
node-boundary outlines mark membership in four significant,
nonredundant representatives: dark violet, cytosolic ribosome; blue, electron
transport chain / oxidative phosphorylation; orange, mitochondrial protein
degradation; and green, cristae formation. Multiple memberships divide the
outline into colored segments. No colored outline means no membership in these
four selected representatives, not no known pathway.

The pathway analysis maps the displayed genes and the full excitatory Bayesian
network to MSigDB C2:CP v2026.1 human symbols. The mapped network genes are the
custom background (6,952 genes); 34 of 35 displayed genes map. One-sided
hypergeometric tests cover all pathways with 15–500 background members (1,739
tests), followed by Benjamini–Hochberg correction across all tests. Displayed
representatives require BH FDR < 0.05 and at least three displayed members. The
complete ORA and exact memberships are exported, and the figure does not imply
pathway activation or causal regulation.

## Visual encoding

### Network panels

- RPL11: black fill, white bold label, largest node.
- Node area and label size: proportional to local displayed degree, with caps
  to prevent hubs from overwhelming the panel; RPL11 remains fixed as largest.
- Node fill summarizes Phase 8 direct-DEG direction within the corresponding
  broad network: orange/red for AD-up only, blue for AD-down only, split or
  purple for both directions across contrasts, and light gray for no stored
  direct-DEG evidence.
- Recurrent core MitoCarta query hits: solid dark border, with supporting-run
  fraction encoded by a redundant outer ring or adjacent count label.
- Cytosolic ribosomal intermediates: a distinct node shape or double-border
  symbol that does not override the DEG-direction fill.
- Other intermediates: use the DEG-direction fill above, with light neutral
  gray reserved for nodes lacking stored direct-DEG evidence.
- Upstream context: white or very light gray, placed in a dedicated upstream
  sector, with arrows pointing toward RPL11.
- Downstream path edges: darker arrows pointing away from RPL11; direct versus
  multi-step relationships remain evident from distance from the centered
  RPL11 node.
- Edges: arrows with adequate head size; edge direction must remain visible at
  final print size.
- All node-size, radial-distance, and pathway-outline meanings must be
  explained in a legend outside the graph area.

The layout must be deterministic. Use fixed upstream and downstream sectors
based on signed directed depth, with a recorded random seed only for
within-sector collision resolution. Export the final coordinates to TSV so
the layout can be reproduced and edited in Cytoscape.

### Heatmap and null panels

- Use cividis or a discrete derivative for depth/evidence.
- Use the existing Phase 18 Okabe–Ito colors for broad-network and
  sex/APOE-direction annotation strips.
- Add text, shape, or border redundancy so the figure remains understandable
  in grayscale.
- Use sans-serif typography with no text smaller than 7 points at final size.
- Do not use 3D effects, shadows, or a red–green contrast.

### Query-overlap panels

- Use colorblind-safe blue and orange circles with a neutral overlap region.
- Print exact counts inside regions and supporting-query counts in set labels.
- Use identical gene-universe and inclusion rules across broad networks.
- Do not imply that circle area represents abundance unless the layout is
  explicitly area-proportional.
- For more than three individual query sets, use an UpSet-style plot or binary
  membership matrix rather than overlapping additional circles.

## Implemented workflow

Analysis and source-table script:

```text
scripts/figures/analysis/phase_18_key_driver_selection/plot_phase18_rpl11_deep_dive.py
```

This script uses NetworkX for directed graph operations and Matplotlib for the
remaining multi-panel figures. It owns the consensus node, edge, pathway ORA,
and pathway-membership tables, but it no longer writes the standalone pathway
network image files.

Suggested command from the repository root:

```bash
python -B scripts/figures/analysis/phase_18_key_driver_selection/plot_phase18_rpl11_deep_dive.py \
  --output-dir results/figures/analysis/phase_18_key_driver_selection/RPL11 \
  --png-dpi 450 \
  --visual-review-status complete
```

Standalone-network renderer:

```text
scripts/figures/analysis/phase_18_key_driver_selection/render_phase18_rpl11_cytoscape.py
```

With Cytoscape 3.10.4 running and its local automation endpoint available:

```bash
.venv/bin/python scripts/figures/analysis/phase_18_key_driver_selection/render_phase18_rpl11_cytoscape.py \
  --input-dir results/figures/analysis/phase_18_key_driver_selection/RPL11/excitatory \
  --output-dir results/figures/analysis/phase_18_key_driver_selection/RPL11/excitatory \
  --png-zoom 300
```

The renderer imports the validated 35-node and 34-edge tables, creates a
directed Cytoscape network, computes collision-checked radial coordinates,
applies recorded visual mappings, adds the title and legend annotations in
Cytoscape, and exports PNG, PDF, and SVG. The SVG is the primary editable
vector output. Cytoscape's enhancedGraphics circos chart draws the colored
pathway boundary and splits it into segments for multiple memberships. All
analysis decisions remain in the TSV inputs and script; the `.cys` file is an
editable rendering artifact, not an unrecorded analysis source.

## Declared outputs

### Figures

- `excitatory/phase18_rpl11_excitatory_consensus_network_pathways.png`
- `excitatory/phase18_rpl11_excitatory_consensus_network_pathways.pdf`
- `excitatory/phase18_rpl11_excitatory_consensus_network_pathways.svg`
- `phase18_rpl11_deep_dive.png`
- `phase18_rpl11_deep_dive.pdf`
- `phase18_rpl11_deep_dive.svg`
- `phase18_rpl11_ribosomal_comparison.png`
- `phase18_rpl11_ribosomal_comparison.pdf`
- `phase18_rpl11_ribosomal_comparison.svg`
- `phase18_rpl11_query_overlap.png`
- `phase18_rpl11_query_overlap.pdf`
- `phase18_rpl11_query_overlap.svg`

### Network and figure data

- `excitatory/phase18_rpl11_excitatory_consensus_network_nodes.tsv`
- `excitatory/phase18_rpl11_excitatory_consensus_network_edges.tsv`
- `excitatory/phase18_rpl11_excitatory_consensus_pathway_ora.tsv`
- `excitatory/phase18_rpl11_excitatory_consensus_pathway_membership.tsv`
- `phase18_rpl11_nodes.tsv`
- `phase18_rpl11_edges.tsv`
- `phase18_rpl11_layout.tsv`
- `phase18_rpl11_full_three_layer_nodes.tsv`
- `phase18_rpl11_full_three_layer_edges.tsv`
- `excitatory/phase18_rpl11_excitatory.graphml`
- `astrocyte/phase18_rpl11_astrocyte.graphml`
- `phase18_rpl11_run_target_matrix.tsv`
- `phase18_rpl11_run_annotations.tsv`
- `phase18_rpl11_matched_controls.tsv`
- `phase18_rpl11_matched_null_results.tsv`
- `phase18_rpl11_matching_balance.tsv`
- `phase18_rpl11_ribosomal_comparison.tsv`
- `phase18_rpl11_query_hit_membership.tsv`
- `phase18_rpl11_query_overlap_regions.tsv`

### Documentation and audit files

- `excitatory/phase18_rpl11_excitatory_consensus_network_pathways_cytoscape.cys`
- `excitatory/phase18_rpl11_excitatory_consensus_network_pathways_cytoscape_style.xml`
- `excitatory/phase18_rpl11_excitatory_consensus_network_pathways_cytoscape_export.json`
- `phase18_rpl11_deep_dive_caption.md`
- `phase18_rpl11_deep_dive_methods.md`
- `phase18_rpl11_deep_dive_checks.tsv`
- `phase18_rpl11_deep_dive_manifest.tsv`
- `phase18_rpl11_deep_dive_status.tsv`

## Validation requirements

Generation must stop if any blocking check fails.

### Input and identity checks

- canonical Phase 18 table schema and row count match the validated source;
- 161 included KDA calls are present;
- RPL11 is classified as `non_mt_driver`;
- the excitatory and astrocyte RPL11 contexts remain passing and
  `top5_display = TRUE`; and
- no deprecated Phase 12 selection or figure table is read.

### Topology checks

- full network node/edge counts reproduce the fixed anchors;
- RPL11 in-degree, out-degree, and total degree reproduce the fixed anchors;
- exact layer-1/2/3 node sets are disjoint before cumulative union;
- upstream depth sets are computed on the reversed graph, remain separate from
  downstream KDA sets, and reproduce `RPLP1`/`RPS25` for astrocytes and no
  upstream RPL11 nodes for excitatory neurons;
- every displayed directed path begins at RPL11, ends at a retained target,
  and has length at most 3;
- every displayed intermediate is required by at least one retained shortest
  path; and
- complete GraphML node and edge counts match the complete TSV exports.

### Phase 18 reconciliation checks

- conservative-support counts are exactly 20 excitatory and 3 astrocyte;
- supporting-run layer distributions reproduce 1/19 and 2/1 for layers 2/3;
- reconstructed overlap, neighborhood, fold enrichment, raw P, and run q agree
  with the canonical table;
- recurrent-hit frequencies reproduce the fixed anchors; and
- no cell is populated in the run-target matrix unless the gene is both in
  that run's effective query and selected RPL11 neighborhood.

### Query-overlap checks

- every query-overlap row comes from a conservative-support RPL11 run;
- broad network, fine cell type, sex/APOE group, and direction uniquely identify
  each supporting query;
- excitatory direction unions reproduce 21 AD-up genes, 24 AD-down genes, and
  20 shared genes;
- astrocyte direction unions reproduce 6 AD-up genes, 12 AD-down genes, and
  6 shared genes;
- microglia and oligodendrocytes are shown as one-set summaries, not zero-filled
  two-set Venn diagrams; and
- every plotted region count equals the number of exact gene rows exported for
  that region.

### Pathway-annotation checks

- the MSigDB collection contains 4,115 C2:CP pathways;
- the custom background contains 6,952 mapped excitatory-network genes and 34
  of the 35 displayed genes map;
- 1,739 pathways remain after the 15–500 background-member filter;
- all four selected representatives pass BH FDR < 0.05 and have at least three
  displayed members; and
- the membership table contains 34 gene–pathway rows across 29 displayed genes.

### Matched-null checks

- control genes are unique within every null analysis;
- controls belong to the same broad network and non-MT class;
- every control passes the stated coverage and assessability rules;
- matching features are finite and stored before standardization;
- balance before and after matching is reported;
- empirical-tail denominators equal the number of unique controls plus one;
- Null C contains only curated cytosolic ribosomal proteins; and
- results with fewer than 20 controls are explicitly labeled descriptive.

### Figure checks

- PNG, PDF, and SVG files are nonempty;
- vector outputs retain selectable text and arrowheads;
- the Cytoscape PNG is rendered at 300% zoom and has dimensions 2,385 × 1,686;
- all node labels and legends are readable at final figure size;
- no label overlaps a node or another label;
- arrow direction remains visible in color and grayscale;
- colorblind and grayscale review is recorded; and
- figures contain no language implying that Bayesian-network direction proves
  molecular causality.

## Interpretation limits

- The 23 supporting runs are repeated contexts within two fixed broad Bayesian
  networks, not 23 independent network replications.
- The network orientation is inferred and may not uniquely identify biological
  causal direction.
- A layer-3 association can identify a coherent downstream module without
  implying direct RPL11 regulation of every terminal gene.
- Expression/detection matching controls a major ascertainment concern but
  does not remove every possible confounder.
- The same cohort contributes the KDA queries, matching features, and DEG
  annotations; independent human data and perturbation experiments remain
  necessary.
- RPL11 perturbation can create general ribosomal stress. Experimental support
  should require selective changes in the predicted mitochondrial module at a
  dose that does not simply suppress global translation or viability.

## Completion criteria

The RPL11 deep-dive is complete only when:

1. the directed graphs show auditable paths rather than disconnected target
   labels;
2. both upstream context and downstream KDA paths are visible and cannot be
   confused with one another;
3. the run-target matrix and query-overlap figure explain which genes recur
   across directions and individual queries;
4. topology-, expression/detection-, and ribosomal-matched nulls are shown;
5. the RPL11-specific result is separated from the broader ribosomal module;
6. all declared data, vector figures, methods, captions, and checks are saved
   under the required `RPL11` directory; and
7. all blocking checks pass and final-size visual review is recorded.
