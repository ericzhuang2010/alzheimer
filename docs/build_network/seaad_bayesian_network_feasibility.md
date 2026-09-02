# SEA-AD Bayesian Network Feasibility Assessment

**Assessment date:** August 31, 2026

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
| Original construction procedure | Final ROSMAP edge lists exist | Original RIMBANet code, `prior.txt`, parameter files, and edge-support results are missing |
| Software | NetworkX/KDA code exists | No local RIMBANet or equivalent Bayesian-network learning stack is installed |

SEA-AD now provides processed snRNA-seq, snATAC-seq, and Multiome resources, while its genetics are available under controlled access. See the [SEA-AD data portal](https://brain-map.org/consortia/sea-ad/our-data) and [NIAGADS dataset NG00174](https://dss.niagads.org/datasets/ng00174/).

The important limitation is sample size. The network must treat donors—not nuclei—as independent samples, as already specified in [SEA-AD dataset contents](../validation_human/seaad_dataset_contents.md). Millions of nuclei improve each donor's expression measurement, but they do not turn 78 donors into millions of independent observations.

The existing broad ROSMAP networks contain roughly 5,300–10,400 genes per matching cell type. Learning that many directed relationships from approximately 78 donors is an extreme high-dimensional problem. A network can be computed, but many individual edges and directions would be unstable without strong genetic and regulatory priors.

## Recommended approach

### 1. Recover the original ROSMAP construction materials

Obtain the following from the previous analyst:

- RIMBANet code and version
- `prior.txt`
- `bn.param.txt`
- Blacklist and whitelist rules
- Discretization code
- Maximum-parent setting
- Per-edge recurrence or confidence results

The available description indicates three-state expression discretization, 1,000 RIMBANet reconstructions, recurrence filtering, and cycle removal, but the provenance is incomplete. See [the existing Bayesian-network explanation](../email_notes/email_07252026_explained.md).

### 2. Obtain and match SEA-AD genetics

Obtain controlled access to the SEA-AD WGS data and match it to the A9 expression donors. The official WGS release has 84 donors while the local A9 H5AD describes 83, so donor concordance must be checked explicitly.

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

A SEA-AD Bayesian network is technically possible because the cohort now has expression, chromatin, and matched genetic data. But a trustworthy whole-transcriptome causal network is not currently reproducible from this repository, and the 78-donor sample size makes individual edges exploratory.

The scientifically strongest near-term plan is:

1. Continue independent DEG replication now.
2. Recover the original network-construction workflow and SEA-AD genetics.
3. Pilot one prior-constrained SEA-AD broad-cell network.
4. Decide whether full SEA-AD KDA replication is sufficiently stable.

Without genetic access, an expression-plus-ATAC directed network could still be built, but it should be described as an exploratory SEA-AD regulatory network—not a method-matched, genetics-anchored Bayesian causal network.
