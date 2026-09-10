# SEA-AD network-build documentation

The SEA-AD RIMBANet build completed on September 8, 2026. The canonical,
Git-tracked release is:

```text
data/bayesian_network_seaad/
```

It contains seven cell-type directories and `release_manifest.tsv`. Each
network directory contains the final DAG (`result.links3.links.txt`), edge
support, node/gene/sample manifests, prior summary, topology QC, and network
manifest. Six networks are full-integrative; `Vasculature_cells` is explicitly
exploratory ENCODE-only because no CIT direction passed the unchanged BH FDR
threshold of 0.05.

## Documents to use

- [Build plan and execution record](seaad-rimbanet-build.plan.md): the
  authoritative scientific contract, accepted production results, job IDs,
  implementation history, and exact rerun commands.
- [Scratch reproduction runbook](seaad-rimbanet-scratch-reproduction.md): use
  only to recover or fully rerun the disposable Minerva scratch tree. It is
  not needed for KDA or other downstream use of the committed networks.
- [Genotype-source decision](seaad-genotype-source-decision.md): records why
  the available `syn49430589` GDA-8 SNP-array VCF replaced the originally
  proposed NG00174 WGS callset, including limitations and frozen identity/QC
  results.

The checksum-frozen execution configs still name
`data/bayesian_network/SEAAD_A9_2024`. That path is intentionally retained as a
compatibility symlink to `data/bayesian_network_seaad`; changing the frozen
configs after execution would invalidate their recorded SHA-256 provenance.

## Final network inventory

| Network | Mode | Final edges |
|---|---|---:|
| Astrocytes | full-integrative | 6,641 |
| Excitatory_neurons | full-integrative | 8,478 |
| Inhibitory_neurons | full-integrative | 8,421 |
| Microglia | full-integrative | 1,279 |
| OPCs | full-integrative | 3,964 |
| Oligodendrocytes | full-integrative | 6,498 |
| Vasculature_cells | exploratory ENCODE-only | 761 |

All seven releases passed independent DAG/topology validation and contain
1,000-search provenance. Network directions are prior-constrained
probabilistic upstream hypotheses, not signed regulatory effects or proof of
causality.

## Removed superseded documents

The pre-build feasibility memo, estimated resource/blocker memo, and binary
Word summary were removed after completion. They duplicated the retained
documents and incorrectly described the validated inputs, runtime, and pilot
as missing or blocked.
