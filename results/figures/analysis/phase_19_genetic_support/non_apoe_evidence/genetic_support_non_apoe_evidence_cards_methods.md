# Figure methods

Tier 1 grades and candidate contexts were read from
`genetic_support_evidence_summary.tsv`; direct FunGen summary records were
checked in `genetic_support_common_variant_evidence.tsv.gz`. Bellenguez regional
minimum P values and lead variants came from
`recovery_regional_gwas_summary.tsv`. Candidate eQTL measurements and frozen
Bonferroni gates came from `recovery_regional_qtl_summary.tsv`, while route
limitations came from `recovery_route_decisions.tsv`. The targeted RPS15 counts
were read from `opc_rps15_evidence_summary.tsv`; its six positive context rows
were deduplicated to three source tracks after removing the candidate-context
prefix. CSF counts came from `endophenotype_gate_decisions.tsv`.

The cards are deliberately equal in size because P values from different
sources and tests are not comparable effect sizes. Values are deterministic
source summaries, so no error bars or significance annotations are applicable.
Color, direct text labels, borders, and card headings provide redundant
encoding. “PP.H4 unavailable” means no valid primary posterior was produced; it
does not mean PP.H4 was estimated as zero. Regional association is described as
locus evidence and not as assignment of the candidate gene.
