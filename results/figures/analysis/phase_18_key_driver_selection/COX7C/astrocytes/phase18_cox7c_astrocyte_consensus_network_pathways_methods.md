# Methods: COX7C astrocyte consensus network

## Consensus reconstruction

The two conservative-support COX7C rows were read from `call_key_driver_returns.tsv`. Each astrocyte Bayesian network was restricted to the run's recorded effective background, and its D2 COX7C neighborhood was reconstructed. Effective query genes came from `kda_signature_members.tsv`. Because COX7C belongs to both mitochondrial queries, it was removed before counting final overlap, matching the Phase 18 self-exclusion rule. The reconstructed overlaps exactly matched the stored final overlap counts of six and eight.

Neighborhood occurrence counts the supporting run-specific D2 neighborhoods containing a gene. Query-hit occurrence separately counts the self-excluded effective queries in which the gene occurred in that neighborhood. The selected threshold is at least one of two runs. It retains ten hits and yields 23 nodes; 2/2 retains four hits and yields 19 nodes. The figure also includes all direct COX7C edges, the upstream chain `RPLP1 -> RPL11 -> COX7C`, and the additional displayed model edge `RPLP1 -> RPL27`.

## Pathway annotations

ORA used the 22 displayed genes represented in MSigDB C2:CP v2026.1. The explicit universe was 5,769 astrocyte Bayesian-network genes represented in that collection. One-sided hypergeometric tests were run for 1,594 pathways with 15-500 mapped background genes, followed by Benjamini-Hochberg correction. The three displayed, nonredundant representatives are ETC / oxidative phosphorylation (10 genes; BH FDR = 3.27e-11), Cristae formation (4 genes; BH FDR = 0.000145), Cytosolic ribosome (4 genes; BH FDR = 0.00722); all meet BH FDR < 0.05. An outline indicates membership, not pathway activity or experimental causality.

## Rendering

The validated graph tables were rendered in Cytoscape 3.10.4 using a deterministic, collision-checked radial layout without guide rings. COX7C is centered, upstream context occupies the left sector, D1 nodes form the inner radial arc, and D2 hits remain near their D1 parents. Node and pathway colors use a colorblind-safe palette. PNG is exported at 300% zoom, PDF and SVG are retained as vector formats, and the editable `.cys` session and visual-style XML are saved beside the figure.
