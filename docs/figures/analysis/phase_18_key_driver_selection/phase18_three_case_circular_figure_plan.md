# Phase 18 Three-Case Circular Figure Plan — Deprecated

> **Deprecated:** Phase 18 now uses two driver classes: `mt_driver` and
> `non_mt_driver`. The former Case 1 and Case 2 are merged before ACAT,
> candidate selection, and ranking. This document and its three-case counts
> are retained only as a record of the earlier figure design. A new two-class
> figure must use `key_driver_significant_returns.tsv` schema
> `phase18_significant_kda_returns_v2`.

## Status and purpose

This document specifies and records the completed generation of three
standalone circular graphs for the validated Phase 18 key-driver results. There
is one graph for each mutually exclusive case in
the [unified key-driver selection proposal](../../../phase_18_key_driver_selection/unified_key_driver_selection_proposal.md):

1. **Case 1:** core MitoCarta driver and in the run query;
2. **Case 2:** core MitoCarta driver and not in the run query; and
3. **Case 3:** driver outside the 1,136-gene core MitoCarta inventory.

Each graph will show at most the top five passing genes for each broad cell
network. The visual form should closely follow the reduced Phase 12 circular
figure:

```text
results/figures/analysis/phase12_kda/reduced_circular_figure/
  phase12_kda_reduced_circular.png
```

The Phase 12 figure is a **visual reference only**. Candidate membership,
rank, q values, case labels, and annotations must come from the validated
Phase 18 production bundle.

## Bottom-line design

Produce three matched circles with the same network order, network colors,
angular geometry, evidence scale, typography, and export size. The only
scientific difference among the circles is the Phase 18 case represented.

Each circle will contain:

- seven broad-network blocks in a fixed clockwise order;
- five fixed display slots per network;
- one neutral radial evidence bar for every displayed candidate;
- an outer color band identifying the broad network;
- outward-facing gene labels ordered by the frozen Phase 18 rank;
- thin gray center links joining the same selected gene across networks within
  that case;
- a small biological-annotation marker where relevant; and
- an explicit empty result for a testable network with no passing candidate.

The figures must not recompute candidate status, ACAT, multiple-testing
correction, or rank. They are renderings of the frozen Phase 18 selection.

## Scientific meaning of the three graphs

### Graph 1: Case 1 — core MitoCarta and in query

Exact case ID:

```text
case1_core_mito_in_query
```

These candidates are core MitoCarta genes that were themselves members of the
run-specific AD mitochondrial query. The plotted Phase 18 evidence has already
had the driver's guaranteed self-overlap removed before its enrichment P value
and fold enrichment were recalculated.

The figure subtitle and caption must state:

> Self-overlap was removed before run-level evidence was combined.

This circle addresses whether an AD-altered mitochondrial gene reaches other
AD-altered mitochondrial genes. It must not imply that query membership itself
is independent evidence.

### Graph 2: Case 2 — core MitoCarta and not in query

Exact case ID:

```text
case2_core_mito_not_in_query
```

These candidates are core MitoCarta genes that were not members of the
relevant run query. This graph shows query-independent evidence for a
mitochondrial component or regulator.

No self-overlap correction is needed for this case because the driver is not
in the query.

### Graph 3: Case 3 — outside core MitoCarta

Exact case ID:

```text
case3_not_core_mito
```

These candidates are outside the fixed 1,136-gene core MitoCarta inventory.
This is the primary graph for claims about candidate regulators outside the
queried mitochondrial program.

The broader `mito_extended` annotation remains a secondary label and does not
move a gene out of Case 3. For example, an extended-reference member remains a
Case 3 candidate because the case definition is based on core MitoCarta
membership.

## Source-of-truth rules

The case definitions and their biological interpretation come from the
proposal. The official candidate membership and order come from the executed
[Phase 18 implementation plan](../../../phase_18_key_driver_selection/phase_18_key_driver_selection_plan.md)
and its validated production tables.

This distinction matters because the implementation plan explicitly overrides
the proposal's earlier tier-first sorting description. The frozen production
rank is:

1. smaller `aggregate_acat_q`;
2. smaller `aggregate_acat_p` when q values tie; and
3. `current_symbol` alphabetically as the final tie-breaker.

Evidence tier, breadth, recurrence, fold enrichment, coverage, and stability
are annotations. They must not be used by the renderer to reorder sectors.

The plotting code must use `current_symbol` for the visible gene label. It
must retain mapping fields in the plotted-data table but must not silently
replace a current symbol with a MitoCarta synonym.

## Authoritative inputs

Primary Phase 18 input root:

```text
results/minerva_production/18_key_driver_selection/
```

Required files:

| File | Figure use |
|---|---|
| `key_driver_status.tsv` | Require one row with `validation_status = validated_complete`, seven included broad networks, three cases, and zero failed checks. |
| `key_driver_checks.tsv` | Require every blocking check to pass. |
| `key_driver_artifacts.tsv` | Verify the recorded hashes of every source table used by the renderer. |
| `key_driver_analysis_manifest.tsv` | Verify the frozen thresholds, ranking order, and display limit of five. |
| `key_driver_case_manifest.tsv` | Obtain the three ordered case IDs, labels, and exact rules. |
| `key_driver_top5.tsv` | Authoritative network-by-case display membership, rank, q value, coverage, evidence tier, and explicit no-result status. |
| `key_driver_figure_data.tsv` | Add supporting groups, directions, and fine cell types to the plotted-data export and methods/caption package. |
| `key_driver_candidates.tsv` | Add genome origin, mtDNA status, MitoCarta mapping, mitochondrial tier, and extended-reference annotation. |

Do not use the Phase 12 circular plotted-data table as a scientific input.
It may be consulted only to reproduce layout conventions and colors.

## Preflight requirements

The renderer must stop before writing any figure if:

1. Phase 18 is not `validated_complete`;
2. any Phase 18 check is missing or failed;
3. the case manifest does not contain exactly the three expected case IDs in
   order 1, 2, and 3;
4. the analysis manifest does not declare display limit 5;
5. the analysis manifest ranking order is not
   `aggregate_acat_q|aggregate_acat_p|current_symbol`;
6. any required source hash differs from `key_driver_artifacts.tsv`;
7. a ranked top-five row cannot be joined one-to-one to
   `key_driver_candidates.tsv` and `key_driver_figure_data.tsv` by broad
   network, case ID, and current symbol;
8. a displayed row is not a `driver_candidate` with `top5_display = TRUE`;
9. a rank is duplicated or falls outside 1–5 within one network and case; or
10. a no-result list contains a gene symbol or numerical evidence value.

## Broad-network scope and order

Use the seven broad networks with included Phase 18 runs, in the same order as
the reduced Phase 12 circle:

1. Astrocytes
2. Excitatory neurons
3. Inhibitory neurons
4. Microglia
5. OPCs
6. Oligodendrocytes
7. Vasculature

Source IDs and display labels are:

| Source ID | Display label | Color |
|---|---|---|
| `Astrocytes` | Astrocytes | `#009E73` |
| `Excitatory_neurons` | Excitatory neurons | `#E69F00` |
| `Inhibitory_neurons` | Inhibitory neurons | `#0072B2` |
| `Microglia` | Microglia | `#CC79A7` |
| `OPCs` | OPCs | `#56B4E9` |
| `Oligodendrocytes` | Oligodendrocytes | `#F0E442` |
| `Vasculature_cells` | Vasculature | `#D55E00` |

CAMs and T cells have zero included Phase 18 runs. As in the reduced Phase 12
figure, do not create sectors for them. State in each caption that their
absence is due to no included runs and is not a negative key-driver result.

## Selection and empty-result rules

For each broad network and case, use the rows already present in
`key_driver_top5.tsv`:

- `ranked_candidates`: display ranks 1 through the declared displayed count;
- `no_passing_candidate`: retain the network block and label it
  `No passing candidate`;
- `not_testable_no_included_runs`: exclude CAMs and T cells from the geometry
  and explain their absence in the caption; and
- never fill an unused slot with a noncandidate.

The phrase "top five" is a display cap. If one to four genes passed, show only
those genes. If no gene passed all three candidate gates, show an explicit
empty network block.

### Frozen current display snapshot

The table below records `total passing candidates / displayed candidates` in
the current validated bundle. It is a reconciliation target, not a list to
hard-code into the renderer.

| Broad network | Case 1 | Case 2 | Case 3 |
|---|---:|---:|---:|
| Astrocytes | 6 / 5 | 2 / 2 | 5 / 5 |
| Excitatory neurons | 19 / 5 | 9 / 5 | 21 / 5 |
| Inhibitory neurons | 12 / 5 | 9 / 5 | 5 / 5 |
| Microglia | 2 / 2 | 1 / 1 | 1 / 1 |
| OPCs | 4 / 4 | 2 / 2 | 4 / 4 |
| Oligodendrocytes | 2 / 2 | 0 / 0 | 1 / 1 |
| Vasculature | 4 / 4 | 0 / 0 | 0 / 0 |
| **Displayed sectors** | **27** | **15** | **21** |

The current explicit empty results are:

- Case 2: Oligodendrocytes and Vasculature;
- Case 3: Vasculature; and
- Case 1: none among the seven included networks.

## Matched circular geometry

### Canvas

- Use a 12 × 7.2 inch landscape canvas comprising a 7.2-inch circular panel
  and a 4.8-inch legend panel on its right.
- Export the PNG at 450 dpi.
- Keep at least 8–10 mm clear margin around radial labels.
- Inspect all formats at final print size; gene text must remain at least
  7 pt.

If labels cannot meet the 7 pt minimum in the 7.2-inch circular panel, enlarge
all three figures together. Do not enlarge only the crowded case.

### Fixed network blocks and display slots

Use identical geometry in all three circles so a network occupies the same
location in every graph:

```text
7 network blocks × 5 display slots = 35 fixed angular slots per circle
```

- Start at 12 o'clock and proceed clockwise.
- Use a 6-degree gap between broad networks.
- Use an approximately 1-degree gap between the five slots within a network.
- Keep all 35 slots the same angular width.
- Place ranks 1–5 clockwise within each network.
- Draw unused positions as a pale background slot without a gene label or
  evidence bar.

Fixed slots prevent the network blocks from changing position or apparent
size merely because one case has fewer passing candidates. Slot width does
not encode network size, candidate count, or evidence.

### Outer network band

Draw a thin colored annular band outside all five slots belonging to one broad
network. Place the network name once at the midpoint of the full network
block. Use dark boundaries around the yellow oligodendrocyte band so it remains
visible on white and in grayscale.

Network identity must remain readable from text and position without relying
on color.

### Evidence ring

Draw one radial bar per displayed candidate in neutral dark navy (`#344E73`).
The bar represents gene-level aggregate ACAT q-value evidence:

```text
uncapped evidence = -log10(aggregate_acat_q)
capped evidence   = min(uncapped evidence, 15)
display score     = capped evidence / 15
```

Use a common cap and scale across all networks and all three cases. Do not
normalize each network to its own strongest gene, because that would make
evidence heights incomparable across the figures.

Recommended reference circles correspond to `-log10(q)` values 5, 10, and 15.
Record the exact uncapped q value and evidence value in the plotted-data table.
The legend must say that bars at the outer cap represent `q <= 10^-15`.

The candidate threshold is q ≤ 0.05, but q alone was not sufficient for
candidate membership: displayed genes also passed the 80% coverage and
conservative-support gates. State this in the caption rather than adding more
rings.

### Gene labels and biological annotation

- Place `current_symbol` outside each occupied slot.
- Keep labels upright by flipping those in the lower half of the circle.
- Order labels by the stored `display_rank`; do not sort them alphabetically
  during rendering.
- Use medium gray text plus a small gray dot for `is_mtdna_gene = TRUE` in
  Cases 1 and 2.
- Use black text for nuclear-encoded candidates.
- In Case 3, add a small outlined diamond to candidates with
  `extended_reference_member = TRUE`; label this marker `mito_extended
  annotation, outside core MitoCarta`.
- Do not use bold, color, or marker size to imply causal importance.

Evidence tier remains in the plotted-data table and caption package. It should
not be another color, ring, or bar style in the main circles.

### Cross-network links

Within each case, connect repeated selected `current_symbol` values across
broad networks using thin gray curves. A link means only:

> The same gene appears among the displayed candidates in more than one broad
> network in this case.

It is not a Bayesian-network edge or an interaction between cell types.

For a gene selected in `m` networks, anchor the gene's largest uncapped
evidence sector and connect it to the other `m - 1` sectors. Do not draw every
pairwise combination. Use 15–25% opacity and no more than about 0.5–0.8 pt at
final size.

Links must never cross between Case 1, Case 2, and Case 3 graphs.

### Empty network blocks

For `no_passing_candidate`:

- retain the network's colored outer band and five pale slots;
- place one small, horizontal or tangential label at the network-block
  midpoint reading `No passing candidate`;
- draw no gene label, evidence bar, biological marker, or center link; and
- preserve the source `empty_result_reason` in plotted data and the caption
  package.

Do not display a zero-height gene bar: no candidate passed, which differs from
a passing candidate with weak evidence.

### Right-side legend

Do not draw an opaque center disk or mask. Leave the central plotting area
open so cross-network connection curves remain visible end to end. Place a
compact legend in a dedicated panel to the right of the circle:

1. colored band = broad network;
2. navy radial height = capped `-log10(ACAT q)`;
3. gray curve = same displayed gene across networks; and
4. case-appropriate biological marker:
   - Cases 1–2: mtDNA-encoded candidate;
   - Case 3: `mito_extended` annotation outside core MitoCarta.

Include `Common scale: 0–15` beneath the right-side legend. The case definition
belongs in the title/subtitle, not as a paragraph inside the circle.
Keep legend rows vertically compact and place each key close to its label. Set
the legend content near the circular panel rather than centering it in the
available right-side whitespace.

## Titles and explanatory text

Use one common main title:

> Phase 18 key-driver candidates across broad cell networks

Use these case lines:

- **Case 1 — core MitoCarta driver in the run query**
- **Case 2 — core MitoCarta driver outside the run query**
- **Case 3 — driver outside the 1,136-gene core MitoCarta inventory**

Use one short shared selection line:

> Up to five passing candidates per network, ranked by aggregate ACAT q value

Add the Case 1 self-overlap sentence beneath its selection line. Keep all
other details in the caption.

## Color and accessibility

- Retain the colorblind-aware Phase 12 network palette only for the outer
  categorical band.
- Use navy for evidence bars, pale gray for unfilled slots, medium gray for
  links and biological markers, and black for text.
- Do not create red-versus-green comparisons.
- Use redundant text labels and fixed network position so color is never the
  only network encoding.
- Verify all three figures in grayscale and with a color-vision-deficiency
  simulation.
- Use a sans-serif font, preferably Arial or Helvetica.
- Use at least 7 pt for gene and legend text, 8–9 pt for network labels, and
  10–12 pt for the title at final size.

## Derived plotted-data contract

Write the plotted-data table before rendering. It should contain exactly 35
slot rows per case, including occupied and unoccupied slots.

Recommended fields:

```text
schema_version
case_order
case_id
case_label
broad_network
network_display_order
display_network
network_color
slot_rank
slot_status
list_status
empty_result_reason
total_passing_candidate_count
displayed_candidate_count
display_rank
current_symbol
mitocarta_canonical_symbol
mapping_status
mito_tier
genome_origin
is_mtdna_gene
extended_reference_member
aggregate_acat_p
aggregate_acat_q
negative_log10_acat_q
capped_negative_log10_acat_q
display_score
coverage_numerator
coverage_denominator
coverage_fraction
conservative_support_count
evidence_tier
supporting_groups
supporting_directions
supporting_fine_cell_types
selected_network_count_within_case
sector_start_degrees
sector_end_degrees
sector_mid_degrees
source_top5_sha256
source_candidates_sha256
source_figure_data_sha256
```

Allowed `slot_status` values:

```text
ranked_candidate
unused_display_slot
no_passing_candidate_slot
```

Also write a compact link table containing case ID, gene, anchor network,
target network, anchor angle, target angle, and link rule. This makes the
center curves auditable without reverse-engineering the SVG.

## Proposed implementation

Implement a dedicated R renderer because the visual reference and reusable
geometry helpers are already in R:

```text
scripts/figures/analysis/phase_18_key_driver_selection/
  visualize_phase18_three_case_circular.R
```

The new renderer may reuse general path, atomic-write, device, color, annular
sector, upright-label, and Bézier-link helpers from:

```text
scripts/figures/analysis/phease12_kda/
  phase12_kda_figure_common.R
  visualize_phase12_kda_reduced_circular.R
```

Do not source the Phase 12 script as a data pipeline or import its selected
genes. Extract or reuse only general rendering helpers.

Suggested command:

```bash
Rscript scripts/figures/analysis/phase_18_key_driver_selection/visualize_phase18_three_case_circular.R \
  --input-dir results/minerva_production/18_key_driver_selection \
  --output-dir results/figures/analysis/phase_18_key_driver_selection/three_case_circular \
  --top-per-network 5 \
  --evidence-cap 15 \
  --png-dpi 450
```

The script should prepare and validate all three case tables first, then render
all three figures. It must not leave a mixed package in which only one or two
cases were successfully updated.

## Output organization

Proposed output directory:

```text
results/figures/analysis/phase_18_key_driver_selection/three_case_circular/
```

Required outputs:

```text
phase18_case1_core_mito_in_query_circular.svg
phase18_case1_core_mito_in_query_circular.pdf
phase18_case1_core_mito_in_query_circular.png

phase18_case2_core_mito_not_in_query_circular.svg
phase18_case2_core_mito_not_in_query_circular.pdf
phase18_case2_core_mito_not_in_query_circular.png

phase18_case3_not_core_mito_circular.svg
phase18_case3_not_core_mito_circular.pdf
phase18_case3_not_core_mito_circular.png

phase18_three_case_circular_plot_data.tsv
phase18_three_case_circular_links.tsv
phase18_three_case_circular_caption.md
phase18_three_case_circular_methods.md
phase18_three_case_circular_sources.tsv
phase18_three_case_circular_checks.tsv
phase18_three_case_circular_generation_log.tsv
phase18_three_case_circular_status.tsv
```

SVG and PDF are the authoritative vector versions. PNG is a high-resolution
review copy. Do not use JPEG.

Write into a sibling staging directory, validate the complete package, and
publish it atomically. Refuse to overwrite a validated output package unless
an explicit replacement workflow is invoked.

## Proposed shared caption

> **Case-specific Phase 18 key-driver candidates across broad brain-cell
> networks.** Each circular graph shows one prespecified relationship between
> a candidate driver and the run-specific mitochondrial query: Case 1 contains
> core MitoCarta genes in the query, Case 2 contains core MitoCarta genes not
> in the query, and Case 3 contains genes outside the 1,136-gene core MitoCarta
> inventory. Within each broad network, up to five genes that passed the 80%
> coverage, conservative-support, and aggregate ACAT q ≤ 0.05 gates are shown
> in frozen q-value rank order; unfilled positions were not backfilled. For
> Case 1, the driver's guaranteed self-overlap was removed before enrichment
> statistics were recomputed. Navy bar height is the common-scale capped
> negative log10 aggregate ACAT q value, and outer colors identify broad
> networks. Gray center links connect repeated displayed genes across networks
> within the same case and are not network edges. Explicit empty blocks mean
> that no gene passed all candidate gates for that network and case. CAMs and
> T cells are absent because they had no included Phase 18 runs, not because a
> negative driver result was observed. These are statistically supported
> network associations and do not establish causal regulation.

Add one final sentence to the Case 3 caption defining the outlined
`mito_extended` marker. Add the mtDNA marker definition to the Case 1 and
Case 2 captions.

## Automated validation checks

The figure package must fail validation unless all of the following pass:

1. all Phase 18 status, manifest, check, and hash preflight rules pass;
2. exactly three case figures are generated;
3. each plotted-data case contains seven networks and 35 fixed slot rows;
4. occupied slot counts reconcile to 27, 15, and 21 for Cases 1, 2, and 3 in
   the current validated bundle;
5. every occupied slot matches `key_driver_top5.tsv` exactly by network, case,
   rank, symbol, P value, q value, coverage, support count, and evidence tier;
6. every occupied slot joins exactly once to the annotation tables;
7. no occupied slot has rank greater than five;
8. displayed ranks are consecutive from 1 within each ranked network-case
   list;
9. every unused rank after the displayed count is an unoccupied slot;
10. Case 2 contains explicit empty blocks for Oligodendrocytes and
    Vasculature;
11. Case 3 contains an explicit empty block for Vasculature;
12. CAMs and T cells have no plotted sectors;
13. every Case 1 candidate is core MitoCarta and every Case 3 candidate is not
    core MitoCarta;
14. evidence bars exactly reproduce the documented cap and transform;
15. links connect identical symbols only, stay within one case, and use
    exactly `m - 1` links for a gene appearing in `m` displayed networks;
16. no empty or unused slot has a bar, symbol, marker, or link;
17. every visible text label is present in the plotted-data or case/network
    manifest;
18. SVG and PDF retain vector text and shapes;
19. PNG dimensions and 450-dpi metadata match the declared canvas;
20. source and output SHA-256 hashes are recorded; and
21. the terminal figure status is written only after all checks pass.

## Manual review checklist

- [x] The three circles have identical network positions and scale.
- [x] Rank 1–5 proceeds clockwise within every network.
- [x] Gene labels are upright, unclipped, and at least 7 pt at final size.
- [x] Empty result blocks cannot be mistaken for zero evidence.
- [x] Pale unused slots do not resemble additional candidates.
- [x] The Case 1 title/caption states that self-overlap was removed.
- [x] The Case 3 marker clearly says `mito_extended` is outside the core case
      definition.
- [x] The common evidence cap is visible in every legend.
- [x] Cross-network links remain subordinate to bars and labels.
- [x] Links cannot be mistaken for network edges.
- [x] Network labels remain readable without color.
- [x] Yellow remains distinct from white in print and grayscale.
- [x] The figures remain interpretable under color-vision-deficiency
      simulation.
- [x] CAMs and T cells are described as not included, not negative.
- [x] No title, legend, or caption uses causal language.
- [x] SVG, PDF, and PNG agree visually.

## Implementation sequence

1. Freeze this plan, file names, colors, geometry, and q-value display cap.
2. Implement Phase 18 status, check, manifest, and source-hash preflight.
3. Join the top-five, figure-data, and candidate-annotation tables.
4. Construct the fixed 35-slot table for each case and write plotted data.
5. Derive and write the within-case cross-network link table.
6. Run all data reconciliation checks before opening a graphics device.
7. Render the three SVG figures from the same drawing function and geometry.
8. Render matching PDF and 450-dpi PNG versions.
9. Write caption, methods, sources, and generation log.
10. Run automated package checks and manual final-size accessibility review.
11. Write the validated terminal status last and publish the package
    atomically.

## Completion criteria

This task is complete only when all three circular graphs:

- represent exactly one Phase 18 case each;
- show no more than five passing candidates per included broad network;
- preserve explicit empty results without backfilling;
- use the frozen Phase 18 q-value ranking and candidate membership;
- share identical geometry and a common quantitative scale;
- remain readable and interpretable at final manuscript size and in
  grayscale;
- reconcile exactly to the validated Phase 18 source bundle; and
- are accompanied by plotted data, link data, caption, methods, provenance,
  checks, generation log, and validated status artifacts.

## Execution record

Completed on 2026-08-14 (America/New_York) with:

```text
Rscript --vanilla \
  scripts/figures/analysis/phase_18_key_driver_selection/\
visualize_phase18_three_case_circular.R
```

The renderer published the package atomically to:

```text
results/figures/analysis/phase_18_key_driver_selection/
  three_case_circular/
```

The final package contains three figures in SVG, PDF, and 450-dpi PNG; 105
fixed slot rows; 63 displayed candidates (Case 1: 27, Case 2: 15, Case 3:
21); 26 within-case cross-network links; plotted and link data; caption;
methods; source and output hashes; a generation log; a check table; and a
terminal `validated_complete` status. All 22 automated checks passed. The
manual review covered final-size color rendering, grayscale rendering, and
protanopia, deuteranopia, and tritanopia simulations.

The package was regenerated on 2026-08-14 after moving the legend from the
center disk to a dedicated right-side panel. The circular panel retained its
original geometry and physical size; the complete canvas changed from
7.2 × 7.2 inches to 9.6 × 7.2 inches. It was regenerated again on the same
date with every legend text element doubled in size. To avoid clipping while
retaining the circle dimensions, the legend panel expanded to 4.8 inches and
the complete canvas to 12 × 7.2 inches. The package was regenerated once more
on 2026-08-14 after removing the opaque center disk, exposing the complete
cross-network connection curves in all three cases.

The package was subsequently regenerated on 2026-08-14 with a more compact
composition: legend-row spacing was reduced by about 30%, legend keys and text
were moved closer together and toward the circle, the title stack was tightened,
and the seven broad cell-type labels were enlarged by 25% and moved slightly
closer to the outer network band.
