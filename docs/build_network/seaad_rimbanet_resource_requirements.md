# SEA-AD RIMBANet Input and Compute Requirements

## 1. Input data status and size

The required production inputs are not all present in the current checkout.

Present locally:

- Cohort, cell-type, and gene manifests: approximately 16 MB
- Reference annotations: approximately 66 MB
- RIMBANet source and legacy binary: approximately 16 MB
- Existing ROSMAP Bayesian networks: approximately 1.2 MB

Missing:

- SEA-AD H5AD: 37.94 GB decimal / 35.3 GiB
- SEA-AD metadata CSV: 1.44 GB decimal / 1.35 GiB
- Seven broad-cell pseudobulk matrices
- NIAGADS NG00174 WGS/PLINK data and donor crosswalk
- Frozen ENCODE TF-target table
- Validated Linux RIMBANet container

NIAGADS does not publish an aggregate size for NG00174. The release includes
84 CRAMs, gVCFs, and project-level VCF/PLINK data. The network workflow needs
the joint genotype calls rather than every CRAM or gVCF, but the exact required
storage cannot be stated until the permitted files are inspected.

This Mac currently has approximately 131 GiB of available storage. The existing
SEA-AD pipeline requires at least 120 GB free before processing. Downloading
the 35.3 GiB H5AD would reduce free space below that threshold.

## 2. CPU and RAM requirements

The current production configuration requests:

- 1 CPU core per RIMBANet search
- 16 GB RAM per search
- 1,000 searches per cell type
- 7,000 searches across seven cell types
- Up to 100 concurrent jobs
- Up to 100 cores and 1.6 TB aggregate RAM when 100 distributed jobs run
  concurrently
- A 24-hour limit per task, pending measurement in the Microglia pilot

The original Wang wrapper requested approximately 6 GB per job, but that may
not be sufficient for the planned 5,000- to 10,000-gene networks. The initial
resource calibration should use:

- Microglia at 5,000 genes: 1 core and 16 GB RAM per job
- Networks approaching 10,000 genes: initially test 1 core and 32 GB RAM per
  job
- Run 10 calibration jobs first and use their measured maximum resident memory
  and elapsed time to set the final LSF request

The aggregate RAM figure is distributed across Minerva compute nodes; it is not
a request for one 1.6 TB node.

## 3. Local machine versus Minerva

The current machine has:

- Apple M4 Pro
- 14 CPU cores
- 24 GB RAM
- Approximately 131 GiB available storage
- ARM64 macOS, while the public RIMBANet executable is Linux x86-64

The local machine is suitable for:

- Pipeline development
- Synthetic and contract tests
- Input audits
- Possibly limited expression preprocessing when external storage is used

Minerva should be used for:

- The 1,000-search Microglia pilot
- The complete seven-network build
- WGS processing and cell-type eQTL/CIT analysis
- Consensus generation and production release validation

Running even one 16 GB search would consume most of the local machine's RAM.
The legacy Linux x86-64 executable would also require a container or emulation
on the ARM64 Mac. Running 7,000 searches locally, mostly sequentially, is not
practical.

Recommended Minerva storage is at least 200-300 GB when only joint genotype
calls and derived files are retained. Substantially more storage would be
needed if per-donor CRAMs or gVCFs were downloaded.

## 4. Current production blockers

The automated prerequisite audit currently reports:

- 14 missing broad-cell pseudobulk files
- No controlled WGS/PLINK input
- No WGS-to-expression donor crosswalk
- No frozen ENCODE TF-target table
- No validated Linux container image

Production execution must remain blocked until these inputs and the Minerva
runtime are identified and checksum-frozen.
