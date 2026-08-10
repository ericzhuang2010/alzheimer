# Phase 12 KDA network figure creation plan

**Plan date:** 2026-08-09  
**Status:** Proposed implementation plan  
**Scope:** Four topology- and ATP-focused figures based on the validated Phase
12 KDA results, Phase 08 differential-expression results, and the fixed
cell-type Bayesian networks.

## Recommendation summary

The Wang paper is almost certainly the paper referenced in the professor's
feedback. Its Figure 6 uses the suggested visual grammar: node and label size
represent network degree, node color represents differential expression, and
enlarged nodes identify key drivers.

Relevant source materials are:

- [`wang_multiscale_modeling.pdf`](../../../related_papers/wang_multiscale_modeling.pdf),
  especially Figures 4 and 6;
- [`DEG-KDA Final Results v2.pdf`](../../../presentations/DEG-KDA%20Final%20Results%20v2.pdf);
- [`phase11_phase12_selected_mitochondrial_connections.md`](../../../analysis/phase11_phase12_selected_mitochondrial_connections.md);
- [`phase12_driver_gene_discussion.md`](../../../analysis/kda/phase12_driver_gene_discussion.md); and
- the validated production bundle under
  `results/minerva_production/12_kda/`.

The existing reduced circular figure answers **which drivers recur**, and the
existing sex/APOE dot heatmap answers **where the candidates are supported**.
The four figures in this plan address the missing questions:

| Priority | Figure | Main question |
|---:|---|---|
| 1 | Wang-style driver subnetworks | How are the highlighted candidates connected to mitochondrial and ATP-synthase genes? |
| 2 | Female-ε2 versus male-ε2 network recoloring | Does the same fixed topology carry opposite DEG states in the two descriptive strata? |
| 3 | ATP-synthase convergence map | Which upstream candidates repeatedly connect to Complex V genes across cell networks? |
| 4 | Connectivity versus KDA evidence | Are the nominated candidates supported beyond simply being high-degree network hubs? |

The first figure should be the primary deliverable. Figure 2 is the strongest
follow-up presentation slide because it joins the Phase 08 sex-reversal result
to Phase 12 topology. Figures 3 and 4 provide cross-network synthesis and an
important hub-bias diagnostic, respectively.

## Scientific interpretation rules shared by all four figures

The implementation and captions must maintain the following distinctions.

1. A directed Bayesian-network edge is a fitted topological relationship. It
   does not establish molecular causality, physical binding, activation, or
   inhibition.
2. An AD-up or AD-down KDA label describes the mitochondrial query signature,
   not the expression direction of the candidate driver.
3. Node fill may show AD-versus-NCI expression direction, but that color must
   not be interpreted as the sign of an outgoing edge.
4. The adjusted KDA P value and fold enrichment apply to the candidate's
   complete enriched downstream neighborhood, not to one displayed edge or
   gene pair.
5. Repeated fine-cell-type calls reuse one fixed broad-cell network. They show
   recurrence of signature enrichment against the same topology, not repeated
   inference of the edge.
6. Primary directional runs are the main evidence. Secondary pooled runs and
   `AD_both_mito` are sensitivity analyses that reuse primary information and
   should not drive the main figures.
7. Sex/APOE contrasts are descriptive. No formal AD-by-sex, AD-by-APOE, or
   three-way interaction was fitted.
8. Male ε2 has 7 AD and 6 NCI donors. Any figure emphasizing this stratum must
   state the donor counts and the need for donor-level sensitivity analysis.

## Shared input data

### Phase 12 KDA

| File | Use |
|---|---|
| `results/minerva_production/12_kda/kda_status.tsv` | Require `validation_status == validated_complete` |
| `results/minerva_production/12_kda/kda_checks.tsv` | Require every validation check to pass |
| `results/minerva_production/12_kda/kda_results.tsv.gz` | Significant candidate rows, best layers, neighborhood sizes, overlap genes, adjusted P values, and fold enrichment |
| `results/minerva_production/12_kda/kda_run_manifest.tsv` | Eligibility, tier, fine-cell type, sex/APOE group, signature direction, and run denominators |
| `results/minerva_production/12_kda/kda_signature_members.tsv.gz` | Effective query membership and candidate-self checks |

Use the compressed production files where both compressed and uncompressed
copies exist. Confirm their hashes against `kda_artifacts.tsv` before figure
preparation.

### Complete candidate-test summaries

| File | Use |
|---|---|
| `results/figures/analysis/phase12_kda/phase12_kda_primary_directional_candidate_tests.tsv.gz` | Complete primary directional candidate-test matrix, including nonsignificant tests |
| `results/figures/analysis/phase12_kda/phase12_kda_mean_of_log_summary.tsv` | Network-standardized MeanOfLog score, ranking coverage, and primary directional recurrence |
| `results/figures/analysis/phase12_kda/phase12_kda_conservative_candidate_summary.tsv` | Existing conservative candidate counts and highlighted-candidate flags |

The complete candidate-test matrix is required for Figure 4. Do not calculate
MeanOfLog using only `kda_results.tsv`, because that file contains only
significant rows.

### Phase 08 differential expression

Use the nine files matching:

```text
results/minerva_production/08_mast/*.yu_mast_de.tsv.gz
```

Required columns are:

```text
cell_type_high_resolution
sex
apoe_group
contrast_id
gene
logFC
fdr_bh_within_contrast
paper_deg
donors_ad
donors_nci
```

Node color should use `logFC`. A redundant black outline should indicate
`paper_deg == TRUE`. This separates effect magnitude from the binary DEG call.

### Bayesian networks

Read the two-column edge lists as directed graphs:

```text
data/bayesian_network/<broad_network>/result.links3.links.txt
```

The main figures require the Astrocytes, Excitatory_neurons,
Inhibitory_neurons, OPCs, Microglia, and Oligodendrocytes networks. Each graph
must remain a directed acyclic graph after loading.

### ATP-synthase definition

Define ATP-synthase-related genes using the MitoCarta pathways in:

```text
results/minerva_production/03_annotations/mitocarta_pathways.tsv
```

Take the union of the `CV subunits` and `CV assembly factors` gene lists. The
current expected union contains 26 genes. Do not define ATP-related genes by a
simple `ATP*` name prefix, because that would mix Complex V biology with
unrelated ATPases and omit non-`ATP`-prefixed assembly factors.

## Shared graph preparation

Implement a reusable preparation module using NetworkX `DiGraph` objects.
For each broad network:

1. load the two-column edge list without changing direction;
2. verify the graph is a DAG;
3. calculate in-degree, out-degree, total degree, and within-network degree
   percentile for every node;
4. reconstruct cumulative directed downstream neighborhoods from layer 1 up
   to layer 3;
5. verify that the reconstructed node count for every selected candidate/run
   equals the published `neighborhood_size` for its `best_layer`;
6. verify that every `overlap_items` gene is present in both the reconstructed
   neighborhood and the effective signature; and
7. calculate reproducible shortest directed paths from each selected driver
   to each highlighted overlap gene.

Use deterministic path ordering and deterministic layouts. If a force-directed
layout is used during exploration, set and record a random seed. The final
subnetwork figures should prefer a left-to-right hierarchical layout because
the networks are directed DAGs.

## Shared visual encodings

### Node fill: differential expression

- Use a colorblind-safe blue–light gray–orange diverging map centered at zero.
- Blue represents lower expression in AD; orange represents higher expression
  in AD.
- Use one fixed symmetric color limit across all panels in a figure. Start
  with `[-1.5, +1.5]` logFC and document any clipping.
- Use light gray for a gene that was tested but is near zero.
- Use white with a gray crosshatch or gray border for unavailable expression,
  rather than treating missing data as zero.

### Node border and shape

- Black outline: `paper_deg == TRUE`.
- Purple double outline: member of the MitoCarta Complex V gene set.
- Diamond or a heavy double border: focal KDA candidate.
- Thick dark outer ring: gene is in `overlap_items` for the displayed run.

Do not use color alone for more than one meaning. The ATP annotation and KDA
candidate status must have redundant non-color encodings.

### Node size

Calculate node size from total degree in the complete broad network, not from
degree in the plotted subgraph. Otherwise, node sizes would change when a
panel is pruned.

Following Wang et al. Figure 6, scale node diameter linearly with link degree.
Because Matplotlib's `node_size` parameter represents marker area rather than
diameter, use the following conversion:

```text
diameter_points = min(24, 7 + total_degree)
area_points_squared = diameter_points^2
```

The 7-point baseline keeps low-degree nodes visible, while the 24-point cap
prevents extreme hubs from dominating a panel. This produces a much stronger
visual distinction than the earlier `log1p(total_degree)` area transform. For
the highlighted candidates, the current network values provide useful
validation examples:

| Network | Gene | In-degree | Out-degree | Total degree | Within-network degree percentile |
|---|---|---:|---:|---:|---:|
| Astrocytes | `APOE` | 2 | 11 | 13 | 98.6 |
| Excitatory neurons | `LAMTOR5` | 1 | 9 | 10 | 98.1 |
| Excitatory neurons | `GABARAPL2` | 3 | 8 | 11 | 98.6 |
| OPCs | `FTL` | 1 | 30 | 31 | 99.6 |

### Edges

- Always draw arrowheads.
- Draw edges on selected driver-to-overlap paths in dark gray or black.
- Draw other displayed neighborhood edges in low-opacity light gray.
- Do not vary underlying Bayesian-edge width as though it represented edge
  confidence; these production edge lists do not contain a confidence weight.
- In Figure 3 only, edge width has a different, explicitly labeled meaning:
  the number of conservative primary directional KDA calls supporting a
  driver/Complex V neighborhood relationship.

### Labels

Always label:

- the focal candidate;
- all Complex V nodes;
- named biological mediators in the slide narrative; and
- intermediate nodes on highlighted paths.

Label other nodes only when space permits. Label size may weakly track node
degree, as in the Wang paper, but it must remain readable at final figure size.

## Figure 1: Wang-style candidate-driver subnetworks

### Question

How do the three highlighted KDA candidates connect to mitochondrial-stress
and ATP-synthase genes in representative primary directional runs?

### Proposed title

> Candidate drivers organize ATP-synthase and mitochondrial-stress
> neighborhoods in AD

### Panel A: astrocyte `APOE`

Use this exact result:

```text
kda_run_id: primary_Ast_GRM3_M_e2_AD_down_mito
key_driver: APOE
fine_cell_type: Ast GRM3
signature_group: M_e2
signature_direction: AD_down_mito
best_layer: 2
neighborhood_size: 19
overlap_count: 5
signature_size: 94
fold_enrichment: 17.12
adjusted_p_value: 0.000411256579874106
overlap_items: ATP5PB;LDHB;TUFM;ATP5F1A;AGT
```

Required highlighted paths are:

```text
APOE -> TUFM
APOE -> ATP5PB
APOE -> LDHB -> ATP5F1A
APOE -> CHCHD10
```

`CHCHD10` is a relevant direct neighbor but is not in the male-ε2 AD-down KDA
overlap. Draw it with the appropriate DEG status but without the KDA-overlap
outer ring.

### Panel B: excitatory-neuron `LAMTOR5`

Use this exact result:

```text
kda_run_id: primary_Exc_L3_4_RORB_CUX2_M_e2_AD_down_mito
key_driver: LAMTOR5
fine_cell_type: Exc L3-4 RORB CUX2
signature_group: M_e2
signature_direction: AD_down_mito
best_layer: 3
neighborhood_size: 27
overlap_count: 8
signature_size: 206
fold_enrichment: 13.98
adjusted_p_value: 0.0000103319433826866
overlap_items: ATP5IF1;TMEM11;CHCHD10;NDUFA6;ATP5MC2;TMEM126A;NDUFB6;MRPL4
```

Required highlighted paths include:

```text
LAMTOR5 -> ATP5IF1
LAMTOR5 -> POP7 -> ATP5MC2
```

### Panel C: excitatory-neuron `GABARAPL2`

Use this exact result:

```text
kda_run_id: primary_Exc_L4_5_RORB_GABRG1_M_e2_AD_down_mito
key_driver: GABARAPL2
fine_cell_type: Exc L4-5 RORB GABRG1
signature_group: M_e2
signature_direction: AD_down_mito
best_layer: 3
neighborhood_size: 45
overlap_count: 9
signature_size: 184
fold_enrichment: 9.90
adjusted_p_value: 0.0000338515924892273
overlap_items: CHCHD2;MRPS18B;IDI1;ARF5;ATP5MC3;PARK7;ACP1;MRPL27;BAX
```

Required highlighted paths are:

```text
GABARAPL2 -> CHCHD2
GABARAPL2 -> MAGEF1 -> SNAPC5 -> PARK7
GABARAPL2 -> NDUFA4 -> ATP5MC3
```

The `ATP5MC3` path extends the slide narrative without replacing the primary
`CHCHD2`/`PARK7` interpretation.

### Layout

- Publication version: three aligned landscape panels with one shared legend
  and one shared logFC colorbar.
- Presentation version: a 2×2 grid with the fourth tile reserved for a large
  encoding legend and a concise interpretation statement.
- Place the driver on the left and downstream nodes toward the right.
- Keep graph scale visually comparable but do not force identical coordinates
  across different broad networks.
- Show all nodes in the 19- and 27-node neighborhoods. For the 45-node
  `GABARAPL2` panel, show every node and edge but restrict text labels to the
  required set unless a final-size review supports more labels.

### Panel annotation

Each panel subtitle should state:

```text
fine cell type | sex/APOE | signature direction
best layer | overlap/neighborhood | BH-adjusted KDA P | fold enrichment
```

Add a caption sentence stating that the adjusted P value and fold enrichment
refer to the complete neighborhood, not the displayed gene pairs separately.

### Acceptance criteria

- Reconstructed neighborhood sizes are exactly 19, 27, and 45.
- All published overlap genes are in the displayed graph and effective query.
- Highlighted paths match the fixed directed networks.
- Node sizes use complete-network degree.
- All three panels use the same DEG color scale.
- `ATP5PB`, `ATP5F1A`, `ATP5IF1`, `ATP5MC2`, and `ATP5MC3` are visually
  identifiable as Complex V genes.

## Figure 2: female-ε2 versus male-ε2 topology recoloring

### Question

Does the same fixed network neighborhood carry opposite AD-associated
expression states in female ε2 and male ε2?

### Proposed title

> Shared candidate-driver topology carries opposite female-ε2 and male-ε2
> expression states

### Layout

Use two columns:

```text
Female ε2, AD-up mitochondrial signature | Male ε2, AD-down mitochondrial signature
```

Use three rows:

1. `APOE`, `Ast GRM3`;
2. `LAMTOR5`, `Exc L4-5 RORB IL1RAPL2`; and
3. `GABARAPL2`, `Exc L4-5 RORB IL1RAPL2`.

For each row, construct one shared graph and calculate its coordinates once.
Reuse the exact node positions, edge paths, node sizes, labels, and color scale
in the female and male panels. Only the DEG fill, binary DEG outline, and
run-specific KDA-overlap ring may change between columns.

### Exact KDA rows

| Driver and fine cell type | Female ε2 AD-up | Male ε2 AD-down |
|---|---|---|
| `APOE`, `Ast GRM3` | layer 1; 3/9 overlap; adjusted P = 0.00314; FE = 37.25 | layer 2; 5/19 overlap; adjusted P = 0.000411; FE = 17.12 |
| `LAMTOR5`, `Exc L4-5 RORB IL1RAPL2` | layer 2; 4/20 overlap; adjusted P = 0.00264; FE = 19.59 | layer 3; 6/27 overlap; adjusted P = 0.0000640; FE = 19.15 |
| `GABARAPL2`, `Exc L4-5 RORB IL1RAPL2` | layer 3; 4/48 overlap; adjusted P = 0.0437; FE = 8.16 | layer 3; 5/48 overlap; adjusted P = 0.0108; FE = 8.98 |

Use the maximum required layer within each row to define the shared displayed
topology: layer 2 for `APOE`, layer 3 for `LAMTOR5`, and layer 3 for
`GABARAPL2`. The run-specific overlap ring must still reflect each run's own
best-layer result.

### Prespecified expression checks

The preparation output should reproduce these values before plotting:

| Fine cell type | Gene | Female ε2 logFC | Male ε2 logFC |
|---|---|---:|---:|
| `Ast GRM3` | `APOE` | +0.785 | -0.506 |
| `Ast GRM3` | `TUFM` | +0.506 | -0.939 |
| `Ast GRM3` | `ATP5PB` | +0.153 | -1.151 |
| `Ast GRM3` | `ATP5F1A` | +0.280 | -0.816 |
| `Exc L4-5 RORB IL1RAPL2` | `LAMTOR5` | +0.505 | -0.928 |
| `Exc L4-5 RORB IL1RAPL2` | `ATP5IF1` | +0.420 | -0.497 |
| `Exc L4-5 RORB IL1RAPL2` | `ATP5MC2` | +0.492 | -0.560 |
| `Exc L4-5 RORB IL1RAPL2` | `GABARAPL2` | +0.463 | -0.573 |
| `Exc L4-5 RORB IL1RAPL2` | `ATP5MC3` | +0.430 | -0.491 |
| `Exc L4-5 RORB IL1RAPL2` | `PARK7` | +0.532 | -0.442 |

The figure should not place asterisks directly beside nodes. Use the common
black DEG outline and explain it in the legend. Include `donors_ad` and
`donors_nci` in the plotted-data table and caption.

### Acceptance criteria

- Coordinates and node sizes are byte-for-byte identical across the two
  columns within each row.
- The expression values above are reproduced from Phase 08.
- The same symmetric color scale is used across all six panels.
- Complex V genes remain identifiable independently of their DEG color.
- Captions call the contrast descriptive and report the male-ε2 donor counts.

## Figure 3: cross-network ATP-synthase convergence map

### Question

Which candidate upstream systems repeatedly place MitoCarta Complex V genes
inside significant downstream KDA neighborhoods?

### Proposed title

> Cell-type-specific candidate systems converge on mitochondrial Complex V

### Evidence filter

Start from significant Phase 12 rows and retain a row only when all conditions
are true:

```text
analysis_tier == primary
signature_direction in {AD_up_mito, AD_down_mito}
key_driver is not mtDNA encoded
key_driver is not in overlap_items
overlap_count >= 2
signature_size >= 10
```

For each retained row, intersect `overlap_items` with the 26-gene Complex V
set. Remove candidate self-membership if present as an additional safeguard.

### Graph definition

Construct a directed summary graph, not a literal induced Bayesian subgraph:

- left nodes are candidate drivers;
- right nodes are Complex V genes;
- an edge means the Complex V gene appeared in the candidate's enriched
  downstream overlap in at least one conservative primary directional run;
- edge width is the number of qualifying runs;
- edge color or a narrow adjacent strip identifies the broad network; and
- edge style records the shortest distance in the fixed Bayesian network:
  solid for one edge, dashed for two edges, dotted for three edges.

If one driver-target pair occurs in multiple broad networks, draw separate
network-colored edges rather than silently combining them.

### Prespecified relationships to reproduce

| Driver | Broad network | Complex V target | Conservative primary directional calls |
|---|---|---|---:|
| `RPL11` | Excitatory neurons | `ATP5PF` | 14 |
| `RPL11` | Astrocytes | `ATP5PF` | 2 |
| `RPL11` | Excitatory neurons | `ATP5ME` | 12 |
| `GABARAPL2` | Excitatory neurons | `ATP5MC3` | 15 |
| `LAMTOR5` | Excitatory neurons | `ATP5IF1` | 12 |
| `LAMTOR5` | Inhibitory neurons | `ATP5IF1` | 3 |
| `LAMTOR5` | Excitatory neurons | `ATP5MC2` | 12 |
| `LAMTOR5` | Inhibitory neurons | `ATP5PF` | 4 |
| `RPS15` | Inhibitory neurons | `ATP5F1E` | 6 |
| `RPS15` | Inhibitory neurons | `ATP5PF` | 6 |
| `APOE` | Astrocytes | `ATP5PB` | 2 |
| `APOE` | Astrocytes | `ATP5F1A` | 1 |
| `FTL` | OPCs | `ATP5IF1` | 1 |
| `FTL` | OPCs | `ATP5MC3` | 1 |
| `FTL` | OPCs | `ATP5PF` | 1 |
| `ANKRD11` | OPCs | `ATP5IF1` | 1 |
| `ANKRD11` | OPCs | `ATP5MC3` | 1 |
| `ANKRD11` | OPCs | `ATP5PF` | 1 |

### Selection and layout

Prepare two versions:

1. **Focused main version:** prespecified biologically interpreted candidates
   from the Phase 12 discussion, including `APOE`, `LAMTOR5`, `GABARAPL2`,
   `RPL11`, `RPS15`, `FTL`, and `ANKRD11`.
2. **Complete supplementary version:** every candidate-target pair that passes
   the filter, ordered by total qualifying call count.

Use a two-column bipartite layout. Group drivers by broad network on the left
and order Complex V genes by total incoming support on the right. Node size
should use full-network degree percentile for drivers and total incoming
summary support for target nodes; the legend must distinguish these two size
definitions.

### Acceptance criteria

- The Complex V set contains the expected 26 genes.
- All displayed pair counts reproduce the preparation table.
- Each displayed pair has a directed path of length at most three in the
  corresponding fixed network.
- Edge width is labeled as recurrence of KDA neighborhood support, not edge
  confidence or independent network replication.
- Main and supplementary versions are generated from the same prepared table.

## Figure 4: connectivity versus KDA evidence

### Question

Are prioritized candidates supported only because they are highly connected,
or do they show unusually consistent KDA evidence relative to other tested
nodes of similar network degree?

### Proposed title

> KDA evidence is related to, but distinguishable from, Bayesian-network
> connectivity

The final wording should be revised if the observed analysis does not support
the second clause.

### Candidate universe

Start from `phase12_kda_mean_of_log_summary.tsv`. Retain network-driver rows
with at least one eligible primary directional test and valid ranking
coverage. Join each row to the complete-network degree table by
`broad_network` and `key_driver`.

Do not limit this figure to significant candidates. The complete tested
candidate universe is required to evaluate hub bias.

### Main panel

Plot:

```text
x = within-network percentile of total degree
y = mean_of_log_score_standardized
color = broad network
point area = primary_directional_recurrence_fraction
```

Label the prespecified candidates:

```text
APOE
LAMTOR5
GABARAPL2
RPL11
RPS15
FTL
ANKRD11
SELENOW
WDR82
SLC11A1
HSPA1A
```

Use direct labels with collision avoidance rather than a large legend of gene
names.

### Supporting panel or inset

Show per-network Spearman correlation between degree percentile and
MeanOfLog score, with the number of tested candidate nodes. Report confidence
intervals from a documented bootstrap if feasible; otherwise report rho,
sample size, and nominal P value with an explicit exploratory label.

Also export a faceted diagnostic version using raw total degree on a
`log10(1 + degree)` axis. This checks that the combined percentile plot is not
hiding different network-specific degree distributions.

### Interpretation rules

- A high-degree, high-evidence point is not automatically artifactual; the
  figure asks whether evidence is fully explained by degree.
- A regression or smoother is descriptive, not a correction for degree.
- Do not residualize or redefine KDA scores in the main figure without a
  separate prespecified analysis.
- Highlighted-gene labels must be applied after calculating all positions and
  metrics, not by manually moving their values.

### Acceptance criteria

- Every plotted score is derived from the complete candidate-test matrix.
- Degree is calculated from the full network and converted to percentile
  within that same network.
- Missing tests remain missing and are not converted to P = 1.
- Network sample sizes and ranking-coverage rules are recorded in the plotted
  data.
- Both the combined percentile plot and raw-degree faceted diagnostic are
  exported.

## Implementation structure

Use Python with NetworkX, pandas, matplotlib, and seaborn. NetworkX 3.5 is
currently available in the project environment. Keep preparation separate
from plotting so all figures consume auditable TSV tables.

Because the current Phase 12 figure scripts live under the existing directory
`scripts/figures/analysis/phease12_kda/`, add the new scripts there unless a
separate cleanup explicitly renames that directory.

Recommended files are:

```text
scripts/figures/analysis/phease12_kda/
├── phase12_kda_network_figure_common.py
├── prepare_phase12_kda_network_figure_data.py
├── plot_phase12_kda_wang_subnetworks.py
├── plot_phase12_kda_sex_reversal_networks.py
├── plot_phase12_kda_atp_convergence.py
└── plot_phase12_kda_connectivity_evidence.py
```

The common module should contain only shared data loading, validation,
styling, node-size scaling, graph extraction, path selection, and export
helpers. Figure-specific selection rules should remain in the corresponding
plot script.

## Planned outputs

Write all new outputs outside the validated nine-file Phase 12 production
bundle:

```text
results/figures/analysis/phase12_kda/network_figures/
├── phase12_kda_wang_subnetworks.pdf
├── phase12_kda_wang_subnetworks.svg
├── phase12_kda_wang_subnetworks.png
├── phase12_kda_wang_subnetworks_nodes.tsv
├── phase12_kda_wang_subnetworks_edges.tsv
├── phase12_kda_sex_reversal_networks.pdf
├── phase12_kda_sex_reversal_networks.svg
├── phase12_kda_sex_reversal_networks.png
├── phase12_kda_sex_reversal_networks_nodes.tsv
├── phase12_kda_sex_reversal_networks_edges.tsv
├── phase12_kda_atp_convergence.pdf
├── phase12_kda_atp_convergence.svg
├── phase12_kda_atp_convergence.png
├── phase12_kda_atp_convergence_complete.pdf
├── phase12_kda_atp_convergence_pairs.tsv
├── phase12_kda_connectivity_evidence.pdf
├── phase12_kda_connectivity_evidence.svg
├── phase12_kda_connectivity_evidence.png
├── phase12_kda_connectivity_evidence_by_network.pdf
├── phase12_kda_connectivity_evidence_points.tsv
└── phase12_kda_network_figures_generation_log.tsv
```

The node tables should include graph metrics, expression values, DEG status,
Complex V membership, KDA-overlap status, plotted coordinates, node-size
values, and labels. The edge tables should include source, target, underlying
network, whether the edge lies on a highlighted path, and the visual style.

## Reproducibility and validation workflow

### Stage 1: input validation

- Confirm Phase 12 status is `validated_complete`.
- Confirm every row in `kda_checks.tsv` passes.
- Confirm the production input hashes match `kda_artifacts.tsv`.
- Confirm all required Phase 08 contrast rows and network files exist.
- Confirm all loaded Bayesian networks are DAGs.

### Stage 2: common data preparation

- Create the full node-degree table for all broad networks.
- Create the 26-gene Complex V annotation table.
- Reconstruct all selected downstream neighborhoods and shortest paths.
- Join Phase 08 expression and donor counts.
- Create the conservative driver-to-Complex-V pair table.
- Create the complete score/degree table for Figure 4.
- Write deterministic intermediate TSV files before plotting.

### Stage 3: plot generation

Generate Figures 1 through 4 from prepared TSV files only. Each plot script
must accept explicit input and output directories, a basename, and figure
format options. It must fail rather than silently continue when an acceptance
check is not met.

### Stage 4: visual quality control

- Inspect SVG or PDF at final publication size.
- Verify a minimum final text size of 7 pt, except unavoidable minor labels
  that must remain at least 6 pt.
- Confirm arrowheads remain visible after reduction.
- Confirm the figures remain interpretable in grayscale.
- Confirm the blue–orange expression scale remains distinguishable under
  common color-vision deficiencies.
- Check that labels do not overlap nodes or panel annotations.
- Compare presentation PNGs at normal slide-viewing distance.

### Stage 5: export

- Export vector PDF and SVG as the authoritative files.
- Export 300-dpi PNG versions for presentations and document previews.
- Do not use JPEG.
- Use consistent fonts, panel labels, colors, and legends across all four
  figures.

## Suggested execution order

1. Implement and test the common graph/data-preparation module.
2. Generate Figure 1 and review it at slide and publication size.
3. Reuse the Figure 1 topology/layout code for Figure 2.
4. Generate the conservative Complex V pair table and Figure 3.
5. Generate the complete score/degree table and Figure 4.
6. Run all acceptance and visual-QC checks.
7. Write final captions and a short figure-explanation document for each
   figure.

This order prioritizes the professor's immediate request while ensuring that
the same validated preparation logic supports the broader synthesis and
diagnostic figures.

## Recommended immediate deliverable

For the next presentation, produce Figure 1 first as a 2×2 slide composition:

- upper left: `APOE`–`TUFM`/`ATP5PB`/`ATP5F1A`;
- upper right: `LAMTOR5`–`ATP5IF1`/`ATP5MC2`;
- lower left: `GABARAPL2`–`CHCHD2`/`PARK7`/`ATP5MC3`; and
- lower right: a large visual-encoding legend plus the statement that
  cell-type-specific candidate systems converge on mitochondrial translation,
  stress control, and ATP synthase.

Use Figure 2 as the following slide to show that the same topology is colored
predominantly AD-up in female ε2 and AD-down in male ε2. Figures 3 and 4 can
then support the manuscript-level cross-network synthesis and robustness
argument.
