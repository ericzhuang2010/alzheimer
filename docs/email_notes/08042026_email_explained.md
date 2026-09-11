# Action plan for the August 4, 2026 email

This should be treated as a figure-generation request, not a request to rerun
KDA or rebuild the networks.

The three highlighted drivers are:

1. `LAMTOR5`
2. Astrocytic `APOE`
3. `GABARAPL2`

They are explicitly listed as the first three targets in
[`section_priority.md`](../analysis/section_priority.md) and analyzed together
in
[`phase11_phase12_selected_mitochondrial_connections.md`](../analysis/phase11_phase12_selected_mitochondrial_connections.md).

## What to generate

Make three driver-centered figures, containing five network panels:

| Driver figure | Bayesian-network panel | Layer-3 graph size | Mitochondrial DEGs to highlight |
|---|---|---:|---:|
| `APOE` | Astrocytes | 58 nodes, 57 edges | 7 |
| `LAMTOR5` | Excitatory neurons | 54 nodes, 56 edges | 17 |
|  | Inhibitory neurons | 62 nodes, 62 edges | 15 |
| `GABARAPL2` | Excitatory neurons | 51 nodes, 51 edges | 13 |
|  | Inhibitory neurons | 16 nodes, 15 edges | 1 |

Use separate excitatory and inhibitory facets rather than merging those
Bayesian networks. This preserves their distinct inferred edges while still
delivering three figures—one per highlighted driver.

## Recommended visual definition

For every panel:

- Center the driver and extract all directed downstream descendants within
  three edges.
- Arrange nodes in rings or columns for layer 0, 1, 2, and 3.
- Show arrows in the direction recorded by the fixed Bayesian network.
- Make the driver a large gold diamond.
- Show non-mitochondrial/non-DEG nodes in light gray.
- Color mitochondrial DEGs by AD direction:
  - AD-up: red/orange
  - AD-down: blue
  - observed in both directions across contexts: purple
- Give genes found in the KDA `overlap_items` a thick outline. This
  distinguishes the genes that actually supported a driver's best-layer
  enrichment from other mitochondrial DEGs present elsewhere in its full
  layer-3 neighborhood.
- Label the driver, mitochondrial DEGs, and the named biological targets:
  - `APOE`: `TUFM`, `ATP5PB`, `ATP5F1A`
  - `LAMTOR5`: `ATP5IF1`
  - `GABARAPL2`: `CHCHD2`, `PARK7`

For the main plot, use only primary, directional KDA contexts (`AD_up_mito`
and `AD_down_mito`). Exclude pooled secondary runs and `AD_both_mito` because
they reuse the primary results and would visually inflate recurrence.

The exact mitochondrial signature membership is already stored in
[`kda_signature_members.tsv`](../../results/minerva_production/12_kda/kda_signature_members.tsv).
The existing extraction logic for cumulative directed neighborhoods is in
[`kda_core.R`](../../scripts/analysis/kda/lib/kda_core.R).

## Deliverables

Produce:

- One composite figure containing all five panels.
- Three standalone figures, one per driver.
- SVG and PDF for editing/publication, plus PNG for emailing.
- Node and edge TSV files so the graphs can also be opened in Cytoscape.
- A short methods/caption file explaining the filtering and colors.
- A validation table recording node counts, edge counts, layer assignments,
  DEG status, direction, and supporting KDA-run count.

The caption must say that arrows represent inferred Bayesian-network
topology—not activation, inhibition, or demonstrated causality—and that DEG
colors summarize multiple cell-type/sex/APOE contexts.

## Suggested reply to the professor

> Yes. I will generate cumulative three-layer downstream subnetworks for
> APOE, LAMTOR5, and GABARAPL2 using the corresponding Bayesian networks. I
> will highlight the mitochondrial AD DEGs by expression direction and
> distinguish the genes contributing directly to the significant KDA
> neighborhoods. Because LAMTOR5 and GABARAPL2 occur in both neuronal
> networks, I will show separate excitatory and inhibitory facets rather than
> merge their edges.
