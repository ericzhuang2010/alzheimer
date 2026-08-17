# Methods: APOE astrocyte consensus network

## End product

The figure is a 19-node, 18-edge directed tree centered on APOE. It includes every direct APOE edge in the full astrocyte Bayesian network (`CKB -> APOE`, `LAPTM4A -> APOE`, and 11 APOE outgoing edges), the second upstream steps `GPX4 -> CKB` and `ITM2B -> LAPTM4A`, and the shortest paths through D2 to the retained query hits.

## Consensus reconstruction and display threshold

Four rows with conservative APOE support in the Astrocytes broad network were read from `call_key_driver_returns.tsv`. For each row, the astrocyte Bayesian network was restricted to that run's recorded effective KDA background. The downstream APOE neighborhood was then reconstructed through its selected final layer (D1 or D2). Neighborhood occurrence counts how many of these four run-specific neighborhoods contain a gene. Query-hit occurrence was separately counted from `published_overlap_items`.

The display threshold is at least one query-hit occurrence among four supporting runs (1/4). Threshold profiling showed: 1/4 retains 7 hits and yields 19 nodes; 2/4 retains 4 hits and yields 17 nodes; 3/4 retains 3 hits and still yields 17 nodes; 4/4 retains 1 hit and yields 16 nodes. Because 2/4 would lose `ATP5F1A`, `CHCHD10`, and `NME3` for only a two-node reduction, 1/4 was chosen to preserve information without making the graph crowded. This is solely a figure inclusion rule, not a new statistical threshold.

## Node and edge encodings

Arrows retain the direction in `data/bayesian_network/Astrocytes/result.links3.links.txt`. APOE-incident edges are darker and thicker. Thick black node borders mark query hits meeting 1/4. For downstream nodes, size and the printed `x/4` value encode supporting-neighborhood occurrence. U1/U2 labels denote upstream graph distance and do not represent downstream KDA occurrence. Node fill summarizes direct differential-expression records in `astrocytes.yu_mast_de.tsv.gz`: orange is AD-up only, blue is AD-down only, yellow is both directions, and gray has no stored direct DEG.

## Pathway annotations

Over-representation analysis used MSigDB C2:CP v2026.1 human gene symbols. The custom universe comprised 5,769 astrocyte Bayesian-network genes represented in the library; all 19 displayed genes mapped. One-sided hypergeometric tests were performed for 1,594 pathways with 15-500 mapped background genes and corrected by Benjamini-Hochberg. The displayed pathway representatives are Amyloid fiber formation (3 genes; BH FDR = 0.167), Cholesterol transport / efflux (2 genes; BH FDR = 0.9), Cristae formation (2 genes; BH FDR = 0.9). No selected theme has BH FDR < 0.05. They were chosen as nonredundant contextual annotations with at least two displayed members; the rings must not be interpreted as significant pathway enrichment, pathway activity, or causality.

## Rendering and limitations

The validated graph tables were rendered in Cytoscape 3.10.4 using a deterministic, collision-checked radial layout. APOE is centered; U1 and U2 occupy the left context sector at radii 300 and 510 Cytoscape units, while D1 and D2 use radii 480 and 720. No guide rings are drawn. Colored outer outlines are rendered with Cytoscape enhancedGraphics. PNG is exported at 300% zoom, PDF and SVG are retained as vector formats, and the editable `.cys` session and Cytoscape visual-style XML are saved beside the figure. The graph is a focused display rather than the full 8,285-node astrocyte network. Bayesian-network direction is a model-derived hypothesis, and all biological interpretations require independent validation.
