# Phase 18 RPL11 deep-dive figure plan

## Status

**Planned; not yet implemented:** 2026-08-15

## Goal

Create an auditable RPL11 figure package that answers three questions:

1. Which mitochondrial-query genes lie downstream of RPL11 in the recorded
   excitatory-neuron and astrocyte Bayesian networks, and through which
   intermediate genes?
2. Which downstream mitochondrial genes recur across the Phase 18
   RPL11-supporting runs, fine cell types, sex/APOE groups, and query
   directions?
3. Is RPL11 more strongly associated with mitochondrial queries than
   comparable genes after accounting for network topology, expression and
   detection, and cytosolic-ribosomal annotation?

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
2. immediate upstream context, drawn in light gray and explicitly marked as
   not part of KDA enrichment;
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

### Step 5 — annotate nodes and edges

Each node table must include:

- `network`
- `gene`
- `minimum_downstream_depth`
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

Each edge table must include source, target, network, source/target depth,
whether the edge is on a retained shortest path, and whether it is an upstream
context edge.

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

### Step 7 — run matched-control specificity analyses

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

### Step 8 — compare RPL11 with other selected ribosomal drivers

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

Recommended layout: 14 × 10 inches, four panels.

#### Panel A — excitatory-neuron directed neighborhood

- Left-to-right layered layout: RPL11, depth 1, depth 2, depth 3.
- Display recurrent mitochondrial hits and every shortest-path intermediate.
- Add a compact evidence strip with `20/97` conservative support, aggregate q,
  and `14/14` stability retention.
- State `19 of 20 supporting runs selected layer 3` directly in the panel.

#### Panel B — astrocyte directed neighborhood

- Use the same visual grammar and depth coordinates as Panel A.
- Show `RPLP1 → RPL11` as light-gray upstream context outside the KDA
  neighborhood.
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

## Visual encoding

### Network panels

- RPL11: black fill, white bold label, largest node.
- Recurrent core MitoCarta query hits: cividis fill scaled by supporting-run
  fraction, plus a solid dark border.
- Cytosolic ribosomal intermediates: pale blue fill plus a ribosomal border
  symbol.
- Other intermediates: light neutral gray.
- Upstream context: white or very light gray with a dashed edge.
- Direct DEG evidence: redundant outer ring; color alone must not carry this
  meaning.
- Edges: arrows with adequate head size; edge direction must remain visible at
  final print size.
- All node-size and ring meanings must be explained in a legend outside the
  graph area.

The layout must be deterministic. Use a fixed layered coordinate assignment
based on minimum directed depth, with a recorded random seed only for
within-layer collision resolution. Export the final coordinates to TSV so the
layout can be reproduced and edited in Cytoscape.

### Heatmap and null panels

- Use cividis or a discrete derivative for depth/evidence.
- Use the existing Phase 18 Okabe–Ito colors for broad-network and
  sex/APOE-direction annotation strips.
- Add text, shape, or border redundancy so the figure remains understandable
  in grayscale.
- Use sans-serif typography with no text smaller than 7 points at final size.
- Do not use 3D effects, shadows, or a red–green contrast.

## Planned implementation

Primary script:

```text
scripts/figures/analysis/phase_18_key_driver_selection/plot_phase18_rpl11_deep_dive.py
```

The script should use NetworkX for directed graph operations and
matplotlib/seaborn for deterministic multi-panel rendering. Cytoscape should
be treated as an optional manual refinement tool, not as the source of
unrecorded analysis decisions.

Suggested command from the repository root:

```bash
python -B scripts/figures/analysis/phase_18_key_driver_selection/plot_phase18_rpl11_deep_dive.py \
  --output-dir results/figures/analysis/phase_18_key_driver_selection/RPL11 \
  --png-dpi 450 \
  --visual-review-status complete
```

The implementation should write to a temporary directory, validate the
complete package, and then replace the declared RPL11 outputs atomically.

## Declared outputs

### Figures

- `phase18_rpl11_deep_dive.png`
- `phase18_rpl11_deep_dive.pdf`
- `phase18_rpl11_deep_dive.svg`
- `phase18_rpl11_ribosomal_comparison.png`
- `phase18_rpl11_ribosomal_comparison.pdf`
- `phase18_rpl11_ribosomal_comparison.svg`

### Network and figure data

- `phase18_rpl11_nodes.tsv`
- `phase18_rpl11_edges.tsv`
- `phase18_rpl11_layout.tsv`
- `phase18_rpl11_full_three_layer_nodes.tsv`
- `phase18_rpl11_full_three_layer_edges.tsv`
- `phase18_rpl11_excitatory.graphml`
- `phase18_rpl11_astrocyte.graphml`
- `phase18_rpl11_run_target_matrix.tsv`
- `phase18_rpl11_run_annotations.tsv`
- `phase18_rpl11_matched_controls.tsv`
- `phase18_rpl11_matched_null_results.tsv`
- `phase18_rpl11_matching_balance.tsv`
- `phase18_rpl11_ribosomal_comparison.tsv`

### Documentation and audit files

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
- PNG is rendered at 450 DPI;
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
2. the run-target matrix explains which genes produce recurrence;
3. topology-, expression/detection-, and ribosomal-matched nulls are shown;
4. the RPL11-specific result is separated from the broader ribosomal module;
5. all declared data, vector figures, methods, captions, and checks are saved
   under the required `RPL11` directory; and
6. all blocking checks pass and final-size visual review is recorded.
