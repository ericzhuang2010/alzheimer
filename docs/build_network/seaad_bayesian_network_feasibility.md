# SEA-AD Bayesian Network Feasibility Assessment

**Assessment date:** August 31, 2026

**Construction-code update:** September 2, 2026

**Minerva storage and genotype-source update:** September 4, 2026

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
| Matched genetics | Shared GDA-8 VCF has 95 samples; strict ID audit matches all 78 primary expression donors one-to-one; the final GRCh38 transformation audit is frozen | Locally accessible; deterministic genotype import and genotype QC remain required |
| Regulatory priors | The 2012 Gerstein ENCODE filtered proximal TIP network and HGNC/GENCODE transformation are checksum-frozen | Ready to stage and verify on Minerva |
| Original construction procedure | Final ROSMAP edge lists and the public RIMBANet wrapper/source are available | The previous analyst's run-specific `prior.txt`, parameter files, and edge-support results are still missing |
| Software | NetworkX/KDA code and pinned Docker/Apptainer recipes exist; public RIMBANet source and Linux binary are available upstream | The production SIF must be built and checksum-frozen under `/sc/arion/scratch/zhuane01/alzheimer`, with both work and scratch roots bound into each job |

SEA-AD provides processed snRNA-seq, snATAC-seq, and Multiome resources. For
this build, the selected matched-genetics source is the locally accessible
Synapse file `syn49430589`, an Illumina Global Diversity Array-8 VCF under
`/sc/arion/projects/adineto/sea_ad/Data/SNP_Genomic_Variants/`. NG00174 WGS
is no longer a production dependency. See the
[SEA-AD data portal](https://brain-map.org/consortia/sea-ad/our-data) and the
[genotype-source decision record](seaad-genotype-source-decision.md).

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

### 2. Harmonize and match SEA-AD SNP-array genetics

Use the shared `syn49430589` GDA-8 VCF. Its 95 sample names contain a numeric
prefix followed by the SEA-AD donor ID; a strict suffix audit matched all 78
primary expression donors one-to-one, with 17 extra array samples excluded.
The source `GDA-8v1-0_d1` coordinates are GRCh37, so freeze the matching
Illumina D2 GRCh38 manifest, remap only unique marker IDs, normalize
alleles/strands against the frozen GRCh38 reference, and apply genotype QC
before eQTL mapping. Stage working and derived genotype matrices under
`/sc/arion/scratch/zhuane01/alzheimer/data/seaad_genotypes/syn49430589/`;
retain source identities, checksums, mapping rules, and the protected crosswalk
persistently because Minerva scratch is disposable.

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

- SEA-AD cis-eQTL and causal-inference-test analysis using matched GDA-8
  genotypes and expression
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

A SEA-AD Bayesian network is technically possible because the cohort has
expression, chromatin, and matched genetic data. The construction code and
validated runtime are available, and the shared GDA-8 VCF matches all 78
primary expression donors. The array, D1/D2 manifests, GRCh38 reference, final
marker transformation, and ENCODE TF-target snapshot are checksum-frozen.
Production remains blocked until deterministic genotype import and genotype QC
are complete; the frozen ENCODE artifact must also be staged in Minerva
scratch before the input audit can pass.
Downloadable/reproducible bulk inputs, the SIF, and run products are staged in
Minerva scratch; only code, frozen provenance, and compact validated releases
remain in the work checkout. The
[scratch reproduction runbook](seaad-rimbanet-scratch-reproduction.md)
documents how each artifact class is restored or regenerated. The 78-donor
sample size and measured-array coverage make individual edges exploratory.

The scientifically strongest near-term plan is:

1. Continue independent DEG replication now.
2. Stage ENCODE and complete the frozen GDA-8 GRCh38 import and genotype QC.
3. Pilot one prior-constrained SEA-AD broad-cell network.
4. Decide whether full SEA-AD KDA replication is sufficiently stable.

If the GDA-8 build conversion, identity, or QC gates fail, an
expression-plus-ATAC directed network could still be built, but it must be
described as an exploratory SEA-AD regulatory network—not a method-matched,
genetics-anchored Bayesian causal network.
