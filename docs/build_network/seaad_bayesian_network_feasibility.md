# SEA-AD Bayesian Network Feasibility Assessment

**Assessment date:** August 31, 2026

**Construction-code update:** September 2, 2026

**Minerva storage update:** September 4, 2026

## Executive conclusion

Yes—in principle, SEA-AD-specific Bayesian networks can be generated. However, a defensible ROSMAP-style causal network cannot be produced from the current checkout alone. This would be a substantial new analysis, not a small extension of the existing KDA workflow.

## What the professor is asking for

The professor's concern is that the current SEA-AD KDA uses Bayesian networks constructed from ROSMAP. Therefore, it validates whether SEA-AD DEGs map onto the same ROSMAP network, but it does not independently reproduce the network or key drivers.

A genuine replication requires:

1. Constructing networks using SEA-AD donor data.
2. Running KDA on those SEA-AD networks.
3. Comparing SEA-AD and ROSMAP key drivers.

That interpretation is documented in the [August 31 meeting summary](../email_notes/meeting_08312026_summary_action_items.md).

## Feasibility assessment

| Requirement | Current status | Assessment |
|---|---|---|
| SEA-AD expression data | A9 H5AD has 1.4 million nuclei, 83 donors, and raw UMIs | Available upstream, but the large H5AD and pseudobulk matrices are not in this checkout |
| Independent network samples | 78 donors in the current analytic cohort | Usable, but small for genome-wide network inference |
| Matched genetics | WGS exists for 84 SEA-AD donors; SNP-array data for 80 | Available through controlled NIAGADS access, but not currently local |
| Regulatory priors | SEA-AD snATAC/Multiome and external TF-target resources exist | Technically available |
| Original construction procedure | Final ROSMAP edge lists and the public RIMBANet wrapper/source are available | The previous analyst's run-specific `prior.txt`, parameter files, and edge-support results are still missing |
| Software | NetworkX/KDA code and pinned Docker/Apptainer recipes exist; public RIMBANet source and Linux binary are available upstream | The production SIF must be built and checksum-frozen under `/sc/arion/scratch/zhuane01/alzheimer`, with both work and scratch roots bound into each job |

SEA-AD now provides processed snRNA-seq, snATAC-seq, and Multiome resources, while its genetics are available under controlled access. See the [SEA-AD data portal](https://brain-map.org/consortia/sea-ad/our-data) and [NIAGADS dataset NG00174](https://dss.niagads.org/datasets/ng00174/).

The construction source is now identified at
[mw201608/BayesianNetwork](https://github.com/mw201608/BayesianNetwork), pinned
for this project at commit
`ebd5f4a6c31da22705622e71b6dc5f1eae195fdd`. It contains the RIMBANet C++
source, a legacy Linux binary, prior/banned-matrix Perl scripts, 1,000-search
job wrappers, and consensus/de-loop scripts. This resolves code availability,
but not exact reproduction of the copied ROSMAP networks because their
run-specific inputs and parameters remain unavailable.

The important limitation is sample size. The network must treat donors—not nuclei—as independent samples, as already specified in [SEA-AD dataset contents](../validation_human/seaad_dataset_contents.md). Millions of nuclei improve each donor's expression measurement, but they do not turn 78 donors into millions of independent observations.

The existing broad ROSMAP networks contain roughly 5,300–10,400 genes per matching cell type. Learning that many directed relationships from approximately 78 donors is an extreme high-dimensional problem. A network can be computed, but many individual edges and directions would be unstable without strong genetic and regulatory priors.

## Recommended approach

### 1. Freeze the public construction workflow and recover run-specific ROSMAP materials

Use the pinned public RIMBANet source for new SEA-AD builds. For exact
reproduction of the existing ROSMAP networks, obtain the following from the
previous analyst:

- `prior.txt`
- `bn.param.txt`
- Blacklist and whitelist rules
- Discretization code
- Maximum-parent setting
- Per-edge recurrence or confidence results

The public wrapper documents three-state expression discretization, 1,000
stochastic searches, bidirectional adjacency recurrence filtering, and legacy
cycle removal. The copied networks' provenance is still incomplete. See [the
existing Bayesian-network explanation](../email_notes/email_07252026_explained.md)
and the accepted SEA-AD implementation plan in this directory.

### 2. Obtain and match SEA-AD genetics

Obtain controlled access to the SEA-AD WGS data and match it to the A9 expression donors. The official WGS release has 84 donors while the local A9 H5AD describes 83, so donor concordance must be checked explicitly. Stage the downloadable working copy and derived genotype matrices under `/sc/arion/scratch/zhuane01/alzheimer/data/seaad_wgs/`; retain source identities and checksums persistently because Minerva scratch is disposable.

### 3. Construct seven broad cell-type networks

Build networks for:

- Astrocytes
- Excitatory neurons
- Inhibitory neurons
- Microglia
- OPCs
- Oligodendrocytes
- Vasculature cells

Use all eligible donors for each network. Do not build separate sex/APOE or supertype networks: those groups are far too small. Fine-cell-type and sex/APOE DEG signatures can subsequently be queried against the appropriate broad network.

### 4. Use donor-level pseudobulk expression

Use donor-by-cell-type raw-UMI pseudobulk profiles. The existing pipeline already defines the required aggregation in the [SEA-AD DEG processing plan](../validation_human/seaad_deg_processing_plan.md).

### 5. Derive directional priors

Use:

- SEA-AD cis-eQTL and causal-inference-test analysis using matched WGS and expression
- SEA-AD ATAC/Multiome regulatory evidence
- ENCODE or another documented TF-target source

### 6. Reproduce the consensus-network procedure

Reproduce the Wang-style consensus process: repeated network inference, edge-recurrence filtering, and removal of weak edges from cycles.

The [Wang paper](../related_papers/wang_multiscale_modeling.pdf) is the most directly relevant construction reference. The [Mathys paper](<../related_papers/mathys single-cell atlas reveals correlates.pdf>) supports donor-level pseudobulk analysis; the Yu paper provides signatures but does not construct a Bayesian network.

### 7. Run a focused pilot first

Start with one cell type—microglia or astrocytes—and a prespecified restricted or module-based gene universe. Evaluate:

- Edge stability across donor bootstraps
- Key-driver rank stability
- Agreement across inference methods
- Enrichment of genetic and ATAC priors
- Robustness to covariate adjustment

Only scale to genome-wide, seven-cell-type networks if that pilot is stable.

## Bottom line

A SEA-AD Bayesian network is technically possible because the cohort now has expression, chromatin, and matched genetic data. The construction code is public, but the required SEA-AD H5AD/pseudobulk, controlled WGS, TF-target snapshot, and built runtime are not present in this checkout. Downloadable/reproducible bulk inputs, the SIF, and run products are staged in Minerva scratch; only code, frozen provenance, and compact validated releases remain in the work checkout. The [scratch reproduction runbook](seaad-rimbanet-scratch-reproduction.md) documents how each artifact class is restored or regenerated and identifies the WGS/ENCODE identities that still must be frozen. The 78-donor sample size also makes individual edges exploratory.

The scientifically strongest near-term plan is:

1. Continue independent DEG replication now.
2. Recover the original network-construction workflow and SEA-AD genetics.
3. Pilot one prior-constrained SEA-AD broad-cell network.
4. Decide whether full SEA-AD KDA replication is sufficiently stable.

Without genetic access, an expression-plus-ATAC directed network could still be built, but it should be described as an exploratory SEA-AD regulatory network—not a method-matched, genetics-anchored Bayesian causal network.
