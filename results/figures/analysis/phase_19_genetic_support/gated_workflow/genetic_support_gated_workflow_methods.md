# Figure methods

The candidate scope was reconstructed from `call_key_driver_returns.tsv` by
filtering `top5_display = TRUE` and deduplicating
`key_driver + broad_network + case_id`. Its SHA-256 was verified as
`b917f70e6edcdf030f63e88ba8fbc5b22b80714599c12c80ea449e8c38bd51d8` and its 47 contexts were required to match the Tier 1
candidate manifest exactly. Counts were validated as 25 unique genes, 27
nuclear contexts/19 genes, and 20 mtDNA contexts/6 genes.

The clinical-AD route count came from `tier2_candidate_route_manifest.tsv`
(27 nuclear candidate contexts multiplied by eQTL and sQTL routes). The 57 CSF
screens came from `endophenotype_gate_decisions.tsv` (19 nuclear genes by three
traits). Dataset names and accessions were read from the Tier 1, Tier 2,
recovery, endophenotype, and RPS15 dataset registries. The pinned FunGen release
was `f6f63fc319a417213cf1e86ec0eb14fcb53d2427`; the displayed GWAS accessions are `GCST90027158`,
`GCST90726396`, `GCST90726397`, and `GCST90726398`. The Bellenguez case/control
counts were intentionally not displayed because published bundle metadata are
inconsistent across two source tables.

All five result-bundle statuses and their blocking validation checks were
required to pass before rendering. The recovery decision rule was required to
be `frozen_gwas_gate_then_complete_qtl_model_then_ld_model_then_h0_h4`. This is a workflow schematic rather than an
attrition or causal diagram, so it contains no effect-size scale, uncertainty
interval, or significance encoding. Source root: `/Users/rzhuang/Documents/VscodeProjects/alzheimer/results`.
