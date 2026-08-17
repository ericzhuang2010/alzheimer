# Methods: SELENOW excitatory-neuron consensus network

Fourteen conservative-support SELENOW rows were read from `call_key_driver_returns.tsv`. For each run, the excitatory-neuron Bayesian network was restricted to its recorded effective background and reconstructed through the stored final D2 or D3 layer. Effective query genes came from `kda_signature_members.tsv`. All reconstructed query-overlap counts matched the stored final overlap counts.

Query-hit recurrence was counted separately from neighborhood occurrence. Threshold profiling showed that 4/14 retains 13 hits and yields 25 nodes/25 edges, whereas 5/14 retains 10 hits and yields 21 nodes/20 edges. The 4/14 cutoff preserves three additional recurrent hits while keeping the display compact. The threshold is a coverage choice, not a statistical test.

Pathway ORA used 23 displayed genes represented in MSigDB C2:CP v2026.1. The explicit universe was 6,952 excitatory-neuron Bayesian-network genes represented in that collection. One-sided hypergeometric tests were run for 1,739 pathways with 15-500 mapped background genes and corrected by Benjamini-Hochberg. The three displayed pathways are contextual nonredundant representatives; none passed BH FDR < 0.05: Respiration / electron transport (5 genes; BH FDR = 0.26), Mitochondrial translation elongation (3 genes; BH FDR = 0.612), Selenium metabolism / selenoproteins (2 genes; BH FDR = 0.875).

The graph was rendered in Cytoscape 3.10.4 with a deterministic, collision-checked radial layout and no guide rings. Colors use a colorblind-safe palette. PNG was exported at 300% zoom; PDF and SVG are vector exports, and the editable `.cys` session and visual-style XML are saved beside the figure.
