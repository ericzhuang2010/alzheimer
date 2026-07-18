# Mitochondria-Focused Sex, APOE, and Alzheimer Disease snRNA-seq Research Plan

## 1. Project Goal

This project will extend the analysis in `Yu_sex_apoe.pdf` by asking how mitochondrial gene expression and mitochondrial pathways differ between Alzheimer disease (AD) and no cognitive impairment (NCI), and whether those differences depend on sex, APOE genotype, and cell type.

The project is not simply a search for genes whose names begin with `MT-`. It will analyze four related but distinct mitochondrial signals:

1. **Mitochondrial DNA-encoded expression:** the 13 protein-coding genes encoded by the mitochondrial genome that are present in the local Seurat objects.
2. **Nuclear-encoded mitochondrial genes:** genes whose products localize to mitochondria, using the curated Human MitoCarta3.0 inventory.
3. **Mitochondrial processes:** oxidative phosphorylation (OXPHOS), electron-transport-chain complexes I-V, mitochondrial translation, mtDNA maintenance, mitophagy, dynamics, transport, apoptosis, reactive oxygen species defense, and related pathways.
4. **Mitochondrial read fraction:** the fraction of each nucleus's UMIs assigned to mitochondrial genes (`percent.mt`). This can reflect mitochondrial biology, RNA quality, cell stress, or a mixture of all three, so it must be interpreted separately from pathway expression.

The principal biological unit is the **donor (`projid`)**, not an individual nucleus. Nuclei from the same donor are repeated observations and cannot be treated as independent human subjects.

## Execution Environments

The research uses one scientific implementation across three execution environments. The **local pilot** is the smaller pilot, **Minerva production** is the full production analysis, and **LSF fallback** is an optional backend only for Minerva production tasks that cannot be completed reliably on the on-demand node.

| Execution environment | Compute resource | Expression input | Scope | Purpose |
| --- | --- | --- | --- | --- |
| **Local pilot** | Local machine with ~15 GiB RAM | `data/processed/Vasculature_cells.rds` (~139 MB; ~0.67 GiB loaded) | 17,974 nuclei, 423 represented donors, 5 fine cell types, at most 30 paper-matched contrasts | Prove the complete workflow and fixed schemas end to end. |
| **Minerva production** | One or more 12-hour node allocations with 192 GiB RAM | All nine RDS files under project-relative `data/processed/` (~34.9 GiB total), processed independently | Approximately 2.3 million nuclei, 427 represented donors, 54 fine cell types, at most 324 paper-matched contrasts, plus all prespecified downstream tasks | Run the complete production manifest, validate outputs, and produce final results using the direct resumable controller. |
| **LSF fallback** | LSF compute jobs, only if needed | Only Minerva production tasks that are incomplete, failed, too slow, or too memory-intensive on the on-demand node | No additional nuclei, donors, cell types, contrasts, or scientific analyses beyond Minerva production | Reuse valid Minerva production outputs and rerun only unresolved tasks with per-job resource requests, longer wall times, arrays, and scheduler-managed retries. |

The local pilot is a full scientific pilot, not a different analysis. Minerva production is expected to analyze the complete approximately 2.3-million-nucleus dataset and run the complete scientific workflow. If every Minerva production manifest task completes and validates, **skip LSF fallback**. LSF fallback adds no scientific scope; it is activated only when Minerva production cannot complete one or more tasks because of wall time, out-of-memory failure, unsuitable direct-node concurrency, interrupted execution, or another documented operational failure. Do not tune scientific thresholds between environments or select tasks based on favorable pilot biology.

## 2. Why This Is a Direct Extension of Yu et al.

Yu et al. analyzed approximately 2.3 million nuclei from 427 ROSMAP donors, retained 276 NCI or AD donors after exclusions, and performed AD-versus-NCI differential expression within six sex-APOE groups and 54 high-resolution cell types. The study used Seurat `FindMarkers` with MAST, adjusted for total RNA count, age at death, and postmortem interval (PMI), then compared response patterns across sex and APOE groups using the Zhang-Yu similarity measure.

The paper already contains several mitochondrial leads:

- `MT-ND2` was the most significant APOE-dependent sex-divergent gene.
- Genes divergent between APOE epsilon4 carriers and APOE epsilon3/epsilon3 were enriched for mitochondrial function, OXPHOS, and electron-transport-chain pathways.
- The discussion explicitly recommends further study of sex- and APOE-dependent mitochondrial function in AD.

The proposed research will therefore keep the paper's cohort construction, sex-APOE groups, cell annotations, and AD-versus-NCI contrasts, but make mitochondrial biology the prespecified focus. It will also add donor-aware pseudobulk analysis as the primary inferential method because the paper does not describe a donor random effect in its cell-level MAST tests.

## 3. Main Questions and Hypotheses

### 3.1 Primary questions

1. Within each high-resolution cell type, does AD alter mitochondrial gene expression or mitochondrial pathways relative to NCI?
2. Are AD-associated mitochondrial changes different in females and males?
3. Are AD-associated mitochondrial changes different among APOE epsilon2 carriers, epsilon3/epsilon3 donors, and epsilon4 carriers?
4. Which mitochondrial changes are shared across cell types, and which are specific to neurons, glia, immune cells, or vascular cells?
5. Does `MT-ND2`, the paper's leading mitochondrial candidate, reproduce under donor-aware analysis?

### 3.2 Secondary questions

1. Does mitochondrial read fraction differ by diagnosis, sex, APOE group, or their interactions?
2. Are mtDNA-encoded and nuclear-encoded OXPHOS components altered in the same direction, suggesting coordinated regulation, or in different directions, suggesting mitonuclear imbalance?
3. Which electron-transport-chain complex contributes most strongly to each sex-APOE-cell-type result?
4. Do mitochondrial pathway changes remain after sensitivity analyses for mitochondrial read fraction, low-quality nuclei, donor cell count, age, PMI, and sequencing batch if batch metadata can be obtained?
5. Are mitochondrial results robust to both paper-like cell-level MAST testing and donor-level pseudobulk testing?

### 3.3 Prespecified hypotheses

- AD-associated mitochondrial responses will differ across sex and APOE groups rather than showing one uniform pan-cell-type effect.
- APOE epsilon4 will be associated with stronger divergence in OXPHOS and stress-response programs, consistent with Yu et al.
- `MT-ND2` will show sex-dependent or APOE-dependent AD effects, although its exact direction may vary by cell type.
- Glial, immune, and vascular populations may show clearer stress and mitophagy signatures, while neuronal populations may show stronger OXPHOS and mitochondrial translation changes.

These are hypotheses, not conclusions. The analysis must report null and inconsistent findings as clearly as positive findings.

## 4. Inputs and Execution-Environment Coverage

All estimates below are rounded binary storage sizes. Large RDS files occupy substantially more memory after decompression.

### 4.1 Inputs shared by the local pilot and Minerva production

| Input | Estimated size | Role |
| --- | ---: | --- |
| `docs/Yu_sex_apoe.pdf` | ~2.3 MB | Reference paper and biological motivation. |
| `docs/Yu_sex_apoe_method.md` | ~11 KB | Extracted summary of the paper's methods. |
| `data/processed/ROSMAP_clinical.csv` | ~328 KB | Donor-level sex, APOE genotype, diagnosis, age at death, PMI, and other clinical fields. |
| `data/processed/cell.meta.data.tsv` | ~168 MB | Cell-level `projid`, fine and broad cell types, RNA counts, detected features, barcodes, and clusters. |
| `scripts/05_normalize_seurat_rds.R` | ~3.9 KB | Existing script that runs Seurat `NormalizeData` while retaining raw counts. |
| `scripts/AD_scRNAseq_companion/00_qc_normalization_cluster.Rmd` | ~8.8 KB | Companion QC and normalization example; it demonstrates `SCTransform`. |
| `scripts/AD_scRNAseq_companion/Section_F_DEG_pipeline.Rmd` | ~3.3 KB | Companion MAST and Wilcoxon `FindMarkers` examples. |
| `scripts/AD_scRNAseq_companion/scPower.ROSMAP.Rmd` | ~14 KB | Companion power-analysis and pseudobulk-related example. |
| `data/reference/gencode/gencode.v44.basic.annotation.gtf.gz` | ~29 MB | Shared project-relative GRCh38/hg38 GENCODE v44 annotation, present under the project root both locally and on Minerva; SHA-256 `3e52f82c63f8fd860bf632ccde10441c05751f4c342ad08c0a98e9e2700171a5`. |

Minerva production and any optional LSF fallback must use the same clinical table, cell metadata, mitochondrial annotations, and analysis revision that passed local pilot. Record checksums in all execution manifests.

### 4.2 Local pilot input

| Local input | Estimated size | Measured coverage |
| --- | ---: | --- |
| `data/processed/Vasculature_cells.rds` | ~139 MB on disk; ~0.67 GiB in R | 33,538 genes, 17,974 nuclei, 423 donors, and 5 fine vascular cell types. |

Vasculature is intentionally the only local pilot expression RDS. Its small size allows the full workflow to be exercised on the local ~15 GiB machine without developing pilot-only logic.

### 4.3 Project-relative inputs for Minerva production and optional LSF fallback

The expression input root is the same project-relative directory locally and on Minerva:

```text
data/processed
```

Run every execution environment from its Alzheimer project root. `config/local_pilot.yml` selects only the Vasculature row from this directory, while `config/minerva_rds_manifest.tsv` selects all nine rows for Minerva production. Optional LSF fallback reuses unresolved rows from the same manifest. Do not fall back to the former absolute shared ROSMAP source path.

Both `config/local_pilot.yml` and `config/minerva_shared.yml` should resolve the same relative input layout:

```yaml
inputs:
  expression_root: data/processed
  clinical_csv: data/processed/ROSMAP_clinical.csv
  cell_metadata_tsv: data/processed/cell.meta.data.tsv
```

| Project-relative RDS file | Estimated size |
| --- | ---: |
| `data/processed/Astrocytes.rds` | ~1.6 GiB |
| `data/processed/Excitatory_neurons_set1.rds` | ~5.7 GiB |
| `data/processed/Excitatory_neurons_set2.rds` | ~9.8 GiB |
| `data/processed/Excitatory_neurons_set3.rds` | ~5.8 GiB |
| `data/processed/Immune_cells.rds` | ~616 MiB |
| `data/processed/Inhibitory_neurons.rds` | ~5.2 GiB |
| `data/processed/OPCs.rds` | ~1.1 GiB |
| `data/processed/Oligodendrocytes.rds` | ~5.0 GiB |
| `data/processed/Vasculature_cells.rds` | ~138 MiB |

Estimated total project-relative expression input for Minerva production: **~34.9 GiB**, representing approximately 2.3 million nuclei. These nine objects cover all 54 high-resolution cell types. An optional LSF fallback uses only the subset whose Minerva production tasks did not validate; it does not introduce another dataset. Do not combine the objects into one Seurat object. Process each RDS independently and combine only compact summaries and results.

## 5. Exact Analytic Cohort

### 5.1 Join key

The bridge between expression and clinical data is `projid`. Convert it to an eight-character string in every table before joining:

```r
normalize_projid <- function(x) {
  stringr::str_pad(as.character(x), width = 8, side = "left", pad = "0")
}
```

This is necessary because some files retain leading zeros while others do not. Never convert the final join key back to numeric.

### 5.2 Exclusion sequence

Apply and record exclusions in this order:

1. Start with the 427 `projid` values represented in the snRNA-seq cell metadata.
2. Retain `cogdx == 1` as NCI and `cogdx == 4` as AD.
3. Exclude the four sex-discordant donors reported by Yu et al.: `50301963`, `11326252`, `15114174`, and `10277308`.
4. Exclude APOE epsilon2/epsilon4 (`apoe_genotype == 24`).
5. Exclude missing APOE genotype.
6. Exclude missing PMI, treating blank strings and `NA` as missing.
7. Confirm that age at death and sex are present.

Derive the analysis fields as follows:

```r
diagnosis = ifelse(cogdx == 1, "NCI", "AD")
sex = ifelse(msex == 0, "Female", "Male")
apoe_group = dplyr::case_when(
  apoe_genotype %in% c(22, 23) ~ "e2",
  apoe_genotype == 33 ~ "e33",
  apoe_genotype %in% c(34, 44) ~ "e4",
  TRUE ~ NA_character_
)
```

### 5.3 Required cohort checkpoint

The local metadata reproduces this 276-donor table exactly:

| Sex | APOE group | NCI | AD | Total |
| --- | --- | ---: | ---: | ---: |
| Female | epsilon2 carrier | 17 | 8 | 25 |
| Female | epsilon3/epsilon3 | 45 | 37 | 82 |
| Female | epsilon4 carrier | 11 | 26 | 37 |
| Male | epsilon2 carrier | 6 | 7 | 13 |
| Male | epsilon3/epsilon3 | 53 | 29 | 82 |
| Male | epsilon4 carrier | 10 | 27 | 37 |
| **Total** |  | **142** | **134** | **276** |

The 276-donor table is the global cohort checkpoint and must be reproduced from the master cell and clinical metadata in local pilot and Minerva production, and again for any affected task rerun through LSF fallback. Expression analyses then intersect that cohort with donors represented in each RDS.

For the local pilot Vasculature RDS, the verified expression-represented checkpoint is 274 eligible donors:

| Sex | APOE group | NCI | AD | Total |
| --- | --- | ---: | ---: | ---: |
| Female | epsilon2 carrier | 17 | 8 | 25 |
| Female | epsilon3/epsilon3 | 45 | 36 | 81 |
| Female | epsilon4 carrier | 11 | 26 | 37 |
| Male | epsilon2 carrier | 6 | 7 | 13 |
| Male | epsilon3/epsilon3 | 52 | 29 | 81 |
| Male | epsilon4 carrier | 10 | 27 | 37 |
| **Total** |  | **141** | **133** | **274** |

Two globally eligible donors are absent from Vasculature: female epsilon3/epsilon3 AD donor `20261901` and male epsilon3/epsilon3 NCI donor `11072071`. Their absence is expected. Both Minerva phases must reproduce the global 276-donor cohort and record per-RDS donor intersections.

Do not proceed if the global cohort does not contain 276 donors or if the local pilot Vasculature intersection does not contain 274. The male epsilon2 stratum is especially small; some fine cell types may have fewer than six NCI or seven AD donors after cell-count filtering.

### 5.4 Age and PMI handling

- Convert numeric ages directly.
- ROSMAP may represent ages above 90 as `90+`. Create a documented capped numeric variable such as `age_death_numeric = 90` for these records and add an `age_90plus` indicator for sensitivity analysis.
- Inspect PMI for missing, impossible, and extreme values. Use a scaled continuous PMI in the main model and test robustness to a log transformation if its distribution is strongly right-skewed.
- Scale continuous covariates using the analytic cohort mean and standard deviation so model coefficients are numerically stable.

## 6. Define the Mitochondrial Feature Sets Before Testing

Feature sets must be frozen before examining disease p-values. Save the source, version, download date, gene identifier, and mapping decisions.

### 6.1 mtDNA-encoded protein genes

The 13 canonical mitochondrial protein-coding genes observed in the inspected Vasculature object are:

`MT-ND1`, `MT-ND2`, `MT-CO1`, `MT-CO2`, `MT-ATP8`, `MT-ATP6`, `MT-CO3`, `MT-ND3`, `MT-ND4L`, `MT-ND4`, `MT-ND5`, `MT-ND6`, and `MT-CYB`.

Verify this list separately in every RDS. Report which mitochondrial rRNA and tRNA genes are absent rather than assuming they were measured. Gene-count RDS objects do not support analysis of mtDNA sequence variants, heteroplasmy, deletions, or mitochondrial copy number; those questions require suitable BAM/CRAM, FASTQ, DNA-sequencing, or dedicated variant data.

### 6.2 Nuclear-encoded mitochondrial genes

Use [Human MitoCarta3.0](https://www.broadinstitute.org/files/shared/metabolism/mitocarta/human.mitocarta3.0.html), which contains 1,136 nuclear and mtDNA genes with evidence of mitochondrial localization and pathway/subcompartment annotations. Save the original table and an immutable analysis-ready TSV. Intersect symbols with each Seurat object's row names and report matched, unmatched, duplicated, and aliased symbols.

### 6.3 Prespecified pathway groups

At minimum, create gene sets for:

- OXPHOS complexes I, II, III, IV, and V separately.
- Combined OXPHOS and respirasome assembly.
- Mitochondrial ribosome and mitochondrial translation.
- mtDNA replication, repair, transcription, and RNA processing.
- Protein import, folding, proteostasis, and mitochondrial unfolded-protein response.
- Fusion, fission, cristae organization, transport, and mitophagy.
- Reactive oxygen species production and detoxification.
- Apoptosis and permeability transition.
- Fatty-acid oxidation, TCA cycle, amino-acid metabolism, and metabolite transport.

MitoCarta's hierarchical `MitoPathways` should be the primary annotation. MSigDB C2:CP and GO mitochondrial terms can provide secondary, comparable pathway analyses.

### 6.4 Background universes

Use the correct background for each question:

- Gene-level testing background: genes that pass the expression filter in that cell type and contrast.
- Mitochondrial enrichment background: all tested genes, not all genes in the human genome.
- MitoCarta subpathway testing background: MitoCarta genes that were measured and eligible for that comparison.

## 7. Phase 00: Reproducible Computing Setup

The document uses the named execution environments **local pilot**, **Minerva production**, and **LSF fallback**. Analysis operations use numeric phase identifiers, beginning with Phase 00 for setup and continuing through Phase 15 for figures. Every implemented scientific phase uses the same code in the local pilot and Minerva production; LSF fallback runs only unresolved Minerva production tasks.

| Numeric phase | Controller mode or responsibility | Primary purpose |
| --- | --- | --- |
| **Phase 00** | `environment` | Environment checks, task graphs, and promotion setup. |
| **Phase 01** | `audit` | Audit every Seurat input and write donor inventories. |
| **Phase 02** | `cohort` | Build the global cohort and per-RDS donor intersections. |
| **Phase 03** | `annotations` | Freeze GENCODE, MitoCarta, and tested-gene annotations. |
| **Phase 04** | `qc` | Calculate mitochondrial and raw-count QC metrics. |
| **Phase 05** | `normalize` | Attach metadata and create uniformly normalized working objects. |
| **Phase 06** | `descriptive` | Report donor, nucleus, cell-type, and group coverage. |
| **Phase 07** | `pseudobulk`, `contrasts`, `pseudobulk_de` | Construct pseudobulk counts, freeze contrasts, and fit primary models. |
| **Phase 08** | `mast` | Run the paper-comparable cell-level MAST branch. |
| **Phase 09** | `mito_fraction`, `pathways` | Model mitochondrial read fraction, pathways, and mitonuclear balance. |
| **Phase 10** | `similarity` | Run Zhang-Yu similarity analysis. |
| **Phase 11** | `multiple_testing` | Aggregate completed result branches and apply prespecified global multiple-testing families without changing upstream results. |
| **Phase 12** | `sensitivity` | Run sensitivity and robustness analyses. |
| **Phase 13** | `power` | Run power simulations. |
| **Phase 14** | `parity`, `validate` | Confirm local/Minerva parity and validate completion. |
| **Phase 15** | `figures` | Render final figures and tables from validated inputs. |

Every phase-specific top-level R script begins with its two-digit owning scientific phase. Multiple scripts within one phase share that prefix—for example, Phase 07 uses `07_make_pseudobulk.R`, `07_build_contrast_manifest.R`, and `07_run_pseudobulk_de.R`. Only cross-phase orchestration or handoff utilities, such as `run_pipeline.R` and `run_one_rds.R`, remain unnumbered.

The implemented artifact roots already use the numeric prefixes `00_environment`, `01_audit`, and `02_cohort`. Numeric phase IDs are the plan and runbook taxonomy; the CLI option remains named `--phase` for compatibility, and its value is the controller mode shown above.

The canonical execution-stage names are `local_pilot`, `minerva_production`, and `lsf_fallback`. They are stored in the YAML/task-graph field `execution_stage` and used in task-graph filenames such as `local_pilot_audit_task_graph.tsv` and `minerva_production_audit_task_graph.tsv`. The status field `execution_phase` remains only as a deprecated numeric compatibility code for already-produced outputs; it must not be used in a filename or as an execution-stage name. The controller CLI flag `--phase` selects a scientific task mode such as `audit`, `cohort`, or `mast`, while numeric Phase 00-15 remains the scientific runbook taxonomy.

### 7.1 One implementation across three execution environments

Scientific scripts accept a shared analysis configuration, an input manifest, and an execution configuration. Cohort rules, mitochondrial definitions, normalization, pseudobulk models, MAST settings, contrasts, multiple-testing families, seeds, schemas, and assertions remain identical across local pilot, Minerva production, and any optional LSF fallback.

**The local pilot must be a strict code-path subset of Minerva production.** Every scientific task executed in the local pilot must call the same R script, functions, argument parser, validation logic, and output schema used for the corresponding Minerva production task. The local pilot differs only through configuration and manifest contents: local versus Minerva paths, output roots, one versus nine RDS rows, task/contrast subsets implied by the available cell types, worker and memory limits, and explicitly labeled pilot iteration counts. Do not create a local-pilot-only scientific implementation, copy a scientific script for Minerva production, or branch on `execution_phase` to change an algorithm.

The inclusion rule is:

```text
local pilot scientific task graph = configured subset of Minerva production scientific task graph
local pilot scientific code checksum = Minerva production scientific code checksum
```

Apply the rule as follows:

1. Give every RDS, cell type, contrast, and downstream job a stable task ID. Every local-pilot task ID must occur in the Minerva production manifest, apart from local paths and output roots.
2. Keep all scientific definitions in `config/analysis_parameters.yml`. Environment-specific configuration files may select inputs and task IDs and set operational resources. Any reduced permutation or simulation count must be an explicit pilot configuration value and must produce a `nonfinal_smoke_test` status.
3. Treat `scripts/run_pipeline.R` and `scripts/run_one_rds.R` as orchestration only. They may resolve configs, select manifest rows, launch processes, resume work, and collect statuses; they must not implement normalization, filtering, modeling, pathway analysis, multiple-testing correction, or figure calculations.
4. Invoke the same `scripts/run_pipeline.R` CLI in both primary environments. The controller must invoke the same scientific entry scripts (`scripts/01_*` through `scripts/14_*`) with the same CLI schema. A Minerva production child-process command for the Vasculature row must be reproducible by substituting local-pilot config and manifest paths into the same command template.
5. Record the checksum of every shared scientific script and the resolved scientific configuration in both environment manifests. The local-pilot-to-Minerva-production gate fails if corresponding task code checksums or non-pilot scientific parameters differ.
6. Test the invariant by dry-running the Vasculature task graph under both configs and comparing ordered script names, stable task IDs, argument names, schemas, and scientific checksums. Only configured paths, output roots, resource values, task scope, and declared pilot iteration counts may differ.

#### Plain-language meaning of the promotion check

Before scaling to Minerva production:

- Dry runs list the work each environment would perform; every local pilot task must also appear in Minerva production.
- Matching script checksums prove that corresponding tasks use exactly the same scientific code.
- Matching shared scientific-configuration checksums prove that cohort, normalization, model, contrast, and correction rules are unchanged. Environment-specific path/resource configs and declared pilot limits are expected to differ.
- Matching CLI schemas prove that the same commands and option meanings are used, even when their config values differ.

Promotion succeeds only when Minerva production is the same validated analysis expanded to more inputs and tasks, not a separate implementation.

Only configuration and manifest values differ; scientific source files do not:

- Input and output roots.
- Manifest scope.
- Explicit pilot limits such as permutation or simulation repetitions, always labeled nonfinal.
- Execution backend.
- RAM, CPU, concurrency, temporary-directory, and wall-time limits.
- LSF queue and resource requests in LSF fallback.

Use these planned files:

| Planned configuration | Estimated size | Scope |
| --- | ---: | --- |
| `config/analysis_parameters.yml` | ~5-10 KB | Scientific settings shared by local pilot, Minerva production, and any optional LSF fallback. |
| `config/local_pilot.yml` | ~2-5 KB | Local data/output paths, reference to the shared scientific config, one-RDS manifest path, and declared pilot limits. |
| `config/local_pilot_execution.yml` | ~2-5 KB | One-worker local resources, resume, logging, and wall-time settings using the same execution-config schema as Minerva production. |
| `config/local_pilot_rds_manifest.tsv` | ~1 KB | One Vasculature row. |
| `config/minerva_shared.yml` | ~2-5 KB | Minerva execution/output settings; the expression input root is the same project-relative `data/processed/` used locally. |
| `config/minerva_rds_manifest.tsv` | ~2-5 KB | Fixed nine-RDS row order using `data/processed/<file>.rds` paths and measured resource fields. |
| `config/minerva_production_execution.yml` | ~2-5 KB | Full-production direct-node manifest and twelve-hour, 192 GiB allocation limits. |
| `config/phase3_lsf.yml` | ~2-5 KB | Optional fallback LSF queues, arrays, memory tiers, and wall times. Create only if Minerva production leaves unresolved tasks. |

New task graphs record the named `execution_stage` as well as the deprecated numeric compatibility field `execution_phase`. Every output/status row records its backend, run ID, stable task ID, scientific script path, scientific code-bundle checksum, resolved scientific-configuration checksum, manifest checksum, peak RAM, elapsed time, and validation status.

### 7.2 Local pilot

Run the complete workflow on `data/processed/Vasculature_cells.rds` (~139 MB; ~0.67 GiB loaded) from the local project root:

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer
R --version
Rscript --version
Rscript -e 'packageVersion("Seurat")'
free -h
df -h .
```

Use one worker and write under `results/local_pilot/` (estimated ~0.2-2 GB). Similarity, sensitivity, and power may use reduced limits declared in `config/local_pilot.yml`, but the algorithms, argument schema, scientific definitions, and output schema must match Minerva production. Reduced outputs must be labeled `nonfinal_smoke_test`.

The workstation-only files `config/local_pilot.yml`, `config/local_pilot_execution.yml`, and `config/local_pilot_rds_manifest.tsv` are intentionally listed in `.gitignore`; they are not synchronized to Minerva. Minerva uses `config/minerva_shared.yml`, `config/minerva_production_execution.yml`, and `config/minerva_rds_manifest.tsv`. All pipeline files under `scripts/` remain shared and tracked because Minerva production must execute the same promoted scientific and orchestration code that passed the local pilot.

Run the same controller and phase sequence used by Minerva production; only the config paths differ:

```bash
/usr/bin/time -v Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase all
```

The local pilot ends only after a clean rerun reproduces the 276-donor global cohort, 274-donor Vasculature intersection, count conservation, normalization checks, pilot pseudobulk/MAST outputs, and deterministic status manifests.

### 7.3 Minerva production

Use an allocated Minerva compute node with **192 GiB RAM for 12 hours**. Never run this work on a login node. Minerva production owns the full production manifest: all nine RDS files, approximately 2.3 million nuclei, all 54 fine cell types, every eligible contrast, and all prespecified downstream analyses. The controller is resumable, so use additional on-demand allocations when ordinary continuation is sufficient.

Load the promoted R environment and all build-time system dependencies. MPFR 3.1.2 is required because Minerva's GCC 11.2.0 `cc1` executable links to `libmpfr.so.4`; MPFR 4.x provides only `libmpfr.so.6`. Load the site OpenSSL and CMake modules before reloading GCC 11.2.0 so that a dependency module cannot silently leave GCC 14.2 as the active compiler:

```bash
module purge
module -r spider '^R$'
module spider openssl
module spider cmake

module load mpfr/3.1.2
module load openssl
module load cmake
module load R/4.3.3
module load gcc/11.2.0

module -t list
R --version
Rscript --version
gcc --version
g++ --version
cmake --version
pkg-config --modversion openssl
pkg-config --cflags --libs openssl
```

Use the full OpenSSL and CMake module versions shown by `module -t list` in every later Minerva session; record them in the environment manifest. Both `gcc` and `g++` must report 11.2.0. The OpenSSL `pkg-config` output must resolve to one coherent Minerva module installation rather than mixing GCC's stale `include-fixed` OpenSSL headers with `/usr/include` headers.

Before installing any R package, verify that GCC's runtime dependency is resolved and that the compiler can create an object file:

```bash
CC1=/hpc/packages/minerva-centos7/gcc/11.2.0/libexec/gcc/x86_64-pc-linux-gnu/11.2.0/cc1
ldd "$CC1" | grep -E 'mpfr|not found'

printf 'int main(void) { return 0; }\n' |
  gcc -x c -c -o /tmp/minerva_compiler_test.o -

export LD_RUN_PATH="$LD_LIBRARY_PATH"
```

Stop if `libmpfr.so.4` is still `not found`, if the compiler test exits nonzero, if CMake is unavailable, or if the OpenSSL module is incoherent. Do not create an ABI-crossing symlink from `libmpfr.so.4` to `libmpfr.so.6`.


#### Minerva commands for every new node or login session

Module selections and exported shell variables do not carry into a new on-demand allocation, a different compute node, or a new login shell. The project R library under `renv/library/` is shared and does persist, so do not reinstall packages on every login.

The reliable startup method is to load the known-good module stack explicitly in every new Minerva compute-node shell. A saved Lmod collection is optional, but do not rely on it unless it restores `Rscript` successfully. Paste this entire block before running any pipeline command:

```bash
cd /sc/arion/work/zhuane01/alzheimer

if ! type module >/dev/null 2>&1; then
  source /etc/profile
fi

module purge
module load mpfr/3.1.2
module load openssl
module load cmake
module load R/4.3.3
module load gcc/11.2.0

module -t list
hash -r
command -v Rscript
Rscript --version

export R_LIBS_USER="$HOME/.Rlib"
export http_proxy=http://proxy.chimera.hpc.mssm.edu:3128
export https_proxy=http://proxy.chimera.hpc.mssm.edu:3128
export all_proxy=http://proxy.chimera.hpc.mssm.edu:3128
export no_proxy="localhost,*.hpc.mssm.edu,*.chimera.hpc.mssm.edu,172.28.0.0/16"

export LD_RUN_PATH="$LD_LIBRARY_PATH"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

# R/4.3.3 is linked to the MKL shipped with Intel Parallel Studio XE 2019.
# Define, but do not globally export, the preload used by Phase 07.3 edgeR.
export MKLROOT=/hpc/packages/minerva-centos7/intel/parallel_studio_xe_2019/compilers_and_libraries/linux/mkl
export MKL_LIB="$MKLROOT/lib/intel64_lin"
source "$MKLROOT/bin/mklvars.sh" intel64
export LD_LIBRARY_PATH="$MKL_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LD_RUN_PATH="$LD_LIBRARY_PATH"
export MKL_PRELOAD="$MKL_LIB/libmkl_gf_lp64.so:$MKL_LIB/libmkl_gnu_thread.so:$MKL_LIB/libmkl_core.so"
export MKL_ENABLE_INSTRUCTIONS=AVX2

mkdir -p results/minerva_production/tmp
export TMPDIR="$PWD/results/minerva_production/tmp"
```

`command -v Rscript` must print a path under `/hpc/packages/minerva-centos7/R/4.3.3/`. Stop if it prints nothing or if `module load R/4.3.3` reports an error. Loading `gcc/11.2.0` last is intentional because another dependency module may otherwise leave GCC 14.2 active.

The site `R/4.3.3` module loads `intel/parallel_studio_xe_2019`; do not additionally load `mkl/2024.1`, `mkl/2025.2`, or another Intel/MKL release into this environment. On Minerva, edgeR's fitting step dynamically loads an MKL architecture component. Without the matching link group in the global loader scope, `libmkl_avx2.so` and `libmkl_def.so` fail with undefined symbol `mkl_sparse_optimize_bsr_trsm_i8`, even though simpler matrix operations may succeed. Therefore Phase 07.3 commands must use the scoped prefix `LD_PRELOAD="$MKL_PRELOAD"`; do not export `LD_PRELOAD` globally for unrelated shell commands. `MKL_ENABLE_INSTRUCTIONS=AVX2` makes the instruction-set choice explicit and reproducible across eligible Minerva nodes. The Phase 07.3 subsection contains the mandatory edgeR preflight.

After the explicit block is verified, saving the module stack is optional:

```bash
module save alzheimer_stage2_r433
```

A later `module restore alzheimer_stage2_r433` is acceptable only when it is immediately followed by `hash -r`, `command -v Rscript`, and `Rscript --version`. If any check fails, use the explicit module-load block above; do not proceed with a partially restored collection.

Before running or resuming a scientific task on the new node, validate the initialized session:

```bash
hostname
git status --short
git rev-parse HEAD

R --version
gcc --version
g++ --version
cmake --version
pkg-config --modversion openssl
pkg-config --cflags --libs openssl

CC1=/hpc/packages/minerva-centos7/gcc/11.2.0/libexec/gcc/x86_64-pc-linux-gnu/11.2.0/cc1
ldd "$CC1" | grep -E 'mpfr|not found'

Rscript -e '
stopifnot(as.character(getRversion()) == "4.3.3")
expected <- c(Seurat = "5.5.1", edgeR = "4.0.16", MAST = "1.28.0")
available <- vapply(names(expected), requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))
stopifnot(all(available))
observed <- vapply(
  names(expected),
  function(package) as.character(packageVersion(package)),
  character(1)
)
print(.libPaths())
print(observed)
stopifnot(identical(observed, expected))
renv::status()
'
```

Expected ready state: the Git revision matches the promoted revision; `R`, `gcc`, and `g++` report 4.3.3, 11.2.0, and 11.2.0 respectively; `libmpfr.so.4` resolves with no `not found` entry; OpenSSL resolves through the saved module; the project renv library is first in `.libPaths()`; Seurat/edgeR/MAST match the locked versions; and `renv::status()` reports a consistent project. The `rl_readline_state` warning may still appear but is non-blocking when R continues and all checks pass.

The proxy variables are required only for external downloads, but exporting them on every compute-node session avoids a later CRAN/Bioconductor failure. Test with `curl -I https://cloud.r-project.org/src/contrib/PACKAGES.gz` before any restore or download. Run `renv::restore()` only when `renv::status()` reports a real inconsistency; otherwise proceed directly to the next dry-run/resume command from Section 23.

#### Minerva on-demand setup and Section 7 preflight

Perform this setup in a terminal attached to the allocated on-demand compute node, not on a login node. Synchronize the Git repository before starting. Git must include `.Rprofile`, `.renvignore`, `renv.lock`, `renv/activate.R`, `renv/settings.json`, `renv/.gitignore`, `config/`, `scripts/`, and any populated `jobs/` files. Do not copy `renv/library/` from the local machine; it contains machine-compiled packages and is intentionally ignored.

From the Minerva project root, verify that the checkout is clean and record the exact commit. It must match the local promoted commit used to create the local pilot reference outputs:

```bash
cd /path/to/alzheimer
hostname
git status --short
git rev-parse HEAD
```

Stop if `git status --short` reports an unexplained code or configuration change, if `git rev-parse HEAD` fails, or if the commit differs from the promoted local revision.

After loading `R/4.3.3` as shown above, configure the Minerva compute-node proxy required for CRAN and Bioconductor downloads. Keep these variables exported in the same shell for both the `renv` bootstrap and `renv::restore()`:

```bash
export http_proxy=http://proxy.chimera.hpc.mssm.edu:3128
export https_proxy=http://proxy.chimera.hpc.mssm.edu:3128
export all_proxy=http://proxy.chimera.hpc.mssm.edu:3128
export no_proxy='localhost,*.hpc.mssm.edu,*.chimera.hpc.mssm.edu,172.28.0.0/16'

curl -I https://cloud.r-project.org/src/contrib/PACKAGES.gz
```

Stop and contact Minerva HPC support if the proxy-configured connectivity test fails. Do not interpret CRAN's subsequent `package is not available for this version of R` message as a package compatibility result when the repository index could not be downloaded.

Bootstrap `renv` into the Minerva user library. Temporarily disable the project autoloader for this bootstrap so the command also works when `renv` is not installed yet:

```bash
RENV_CONFIG_AUTOLOADER_ENABLED=FALSE Rscript -e '
lib <- Sys.getenv("R_LIBS_USER")
if (!nzchar(lib)) stop("R_LIBS_USER is empty")
dir.create(lib, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(lib, .libPaths()))
options(timeout = 600)
if (!requireNamespace("renv", quietly = TRUE)) {
  install.packages("renv", repos = "https://cloud.r-project.org", lib = lib)
}
cat("renv version:", as.character(packageVersion("renv")), "\n")
cat("library:", find.package("renv"), "\n")
'
```

Restore the complete project environment from `renv.lock`. A full restore is required rather than installing only three named packages because the environment check and later scientific phases also require `yaml`, `Matrix`, `SeuratObject`, `data.table`, `stringr`, `dplyr`, `readxl`, and their dependencies. Keep the proxy variables, the exact module stack, and `LD_RUN_PATH` active for the entire restore:

```bash
set -o pipefail
Rscript -e 'options(timeout = 1200); renv::restore(prompt = FALSE)' \
  2>&1 | tee renv_restore.log
```

The restore is resumable and may be rerun after correcting a system dependency; successfully installed packages are retained or linked from the renv cache. Known Minerva failure signatures and their required corrections are:

- `libmpfr.so.4: cannot open shared object file`: load `mpfr/3.1.2`, reload `gcc/11.2.0`, and repeat the compiler test.
- `cmake: command not found` while building `fs`: load the CMake module, confirm `cmake --version`, reload `gcc/11.2.0` if the compiler changed, and rerun the restore.
- Conflicting declarations in OpenSSL headers: load one coherent OpenSSL module, verify `pkg-config --cflags --libs openssl`, reload `gcc/11.2.0`, and rerun the restore.
- `No rule to make target 'fast_NN_dist.cpp'` while building Seurat 5.5.1: the extracted source is incomplete. Download the official `Seurat_5.5.1.tar.gz`, require SHA-256 `9614ef02d3e1010c40be5916a309103a76c4221a667cbc4b312e5126459a5821`, verify that it contains `Seurat/src/fast_NN_dist.cpp`, install that archive, and then run `renv::restore(packages = "Seurat", rebuild = TRUE, prompt = FALSE)` to restore CRAN provenance. Do not snapshot the local-tarball provenance into `renv.lock`.

A version-matched package can still be ABI-stale because `renv::status()` checks package records rather than whether an Rcpp module can load. If Seurat reports `Unable to load module "AnnoyAngular": attempt to apply non-function`, rebuild only the locked `RcppAnnoy` package from source against the active locked Rcpp, then test both packages in a fresh R process:

```bash
Rscript -e '
stopifnot(as.character(packageVersion("Rcpp")) == "1.1.2")
options(timeout = 1200)
renv::restore(
  packages = "RcppAnnoy",
  rebuild = TRUE,
  prompt = FALSE
)
'

Rscript -e '
stopifnot(as.character(packageVersion("Rcpp")) == "1.1.2")
stopifnot(as.character(packageVersion("RcppAnnoy")) == "0.0.23")
suppressPackageStartupMessages(library(RcppAnnoy))
suppressPackageStartupMessages(library(Seurat))
cat("RcppAnnoy and Seurat load successfully\n")
'
```

A successful package-only test does not prove that lazy S4 package loading from a serialized Seurat object will work. The shared Phase 01 audit therefore explicitly loads `RcppAnnoy` and then Seurat before `readRDS()`; do not remove or reorder those imports. Validate the serialized-object path with the same order:

```bash
Rscript -e '
suppressPackageStartupMessages(library(RcppAnnoy))
suppressPackageStartupMessages(library(Seurat))
object <- readRDS("data/processed/Astrocytes.rds")
stopifnot(identical(as.integer(dim(object)), c(33538L, 149558L)))
cat("Astrocytes serialized-object load succeeded\n")
'
```

Verify the three principal package versions and the lockfile state:

```bash
Rscript -e '
expected <- c(Seurat = "5.5.1", edgeR = "4.0.16", MAST = "1.28.0")
available <- vapply(
  names(expected),
  requireNamespace,
  quietly = TRUE,
  FUN.VALUE = logical(1)
)
print(available)
if (!all(available)) {
  stop("Missing packages: ", paste(names(expected)[!available], collapse = ", "))
}
observed <- vapply(
  names(expected),
  function(package) as.character(packageVersion(package)),
  character(1)
)
print(observed)
stopifnot(identical(observed, expected))
library(Seurat)
library(edgeR)
library(MAST)
renv::status()
'
```

The expected environment is R 4.3.3 with Bioconductor 3.18, Seurat 5.5.1, edgeR 4.0.16, and MAST 1.28.0. Function-masking messages and the `SummarizedExperiment` import-replacement warning are non-blocking if all packages load. The Minerva `rl_readline_state` ABI warning is also non-blocking for this workflow when R continues successfully, although it should be reported to HPC support. Stop if a version differs, a package does not load, or `renv::status()` lists any missing or inconsistent package; a full-snapshot lockfile is ready only when `renv::status()` reports a consistent project.

Verify that all nine production RDS files and the frozen GENCODE reference exist under the project-relative paths. `data/` and `docs/` are intentionally excluded from Git and must be synchronized separately:

```bash
Rscript -e '
manifest <- read.delim("config/minerva_rds_manifest.tsv", check.names = FALSE)
enabled <- toupper(as.character(manifest$enabled)) %in% c("TRUE", "T", "1", "YES")
paths <- manifest$input_rds[enabled]
missing <- paths[!file.exists(paths)]
if (length(missing)) stop("Missing production RDS files: ", paste(missing, collapse = ", "))
cat("Found", length(paths), "enabled production RDS files\n")
'

GTF=data/reference/gencode/gencode.v44.basic.annotation.gtf.gz
test -r "$GTF"
gzip -t "$GTF"
sha256sum "$GTF"
```

The GENCODE SHA-256 must be `3e52f82c63f8fd860bf632ccde10441c05751f4c342ad08c0a98e9e2700171a5`. `data/reference/Human.MitoCarta3.0.xls` is not required for this Section 7 environment preflight, but it must be downloaded or synchronized before the `annotations` task in Phase 03.

Run only the Section 7 Minerva environment preflight first:

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase environment

Rscript -e '
status <- read.delim("results/minerva_production/00_environment/environment_status.tsv")
print(status)
stopifnot(nrow(status) == 1L, status$validation_status[[1L]] == "validated_complete")
'
```

Do not run the Minerva production `--phase all --dry-run` or execution commands below until the local-pilot promotion gate passes and every referenced scientific script exists with a promoted checksum. A dry run that reports `script_exists = FALSE` or exits nonzero is an implementation stop, not permission to begin production. Before launching production, change `max_total_cores` in `config/minerva_production_execution.yml` only if the actual on-demand allocation has fewer than 48 cores; do not change the shared scientific parameters.

Create `config/minerva_production_execution.yml` (~2-5 KB):

```yaml
execution:
  execution_stage: minerva_production
  execution_phase: 2
  backend: direct
  run_id: minerva_production_192gb_001

  max_total_cores: 48       # Reduce to the actual allocated core count.
  total_memory_gib: 192
  reserve_memory_gib: 32
  walltime_hours: 12
  stop_launching_minutes_before_end: 45

  max_concurrent_rds: 2
  cores_per_rds: 2
  max_concurrent_contrasts: 8
  cores_per_contrast: 1
  max_concurrent_mast_per_rds: 1

  memory_estimate_column: estimated_peak_ram_gib
  default_rds_memory_gib: 96
  default_contrast_memory_gib: 12
  large_job_threshold_gib: 100
  large_jobs_exclusive: true

  resume: true
  fail_fast: false
  poll_seconds: 15
  temp_dir: results/minerva_production/tmp
  log_dir: results/minerva_production/logs

environment:
  OMP_NUM_THREADS: 1
  OPENBLAS_NUM_THREADS: 1
  MKL_NUM_THREADS: 1
```

Create `scripts/run_pipeline.R` (~20-40 KB) during local pilot and use that exact file, without Minerva production edits, for production. It is a generic orchestration controller that launches the shared scientific scripts; all scope and resource differences come from the supplied configs and manifests. It must:

1. Parse the same config, execution-config, manifest, task-mode, and dry-run arguments in every phase.
2. Resolve the manifest subset and construct child commands without changing scientific arguments by phase.
3. Refuse CPU/RAM settings above the configured allocation.
4. Admit a task only when estimated running RAM plus the configured reserve fits within the configured total memory.
5. Run tasks above the configured large-job threshold alone and never load multiple large RDS files in one R session.
6. Stop launching tasks at the configured interval before wall time.
7. Enforce the configured per-RDS MAST concurrency because each worker may load the complete normalized object.
8. Write outputs atomically and skip only validated tasks when resuming.
9. Leave enough time to flush files and write the completion manifest.
10. In dry-run mode, write an ordered task graph containing stable task IDs, scientific script paths, argument names, config checksums, and script checksums so local pilot and Minerva production code-path inclusion can be tested.

Dry-run first:

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase all \
  --dry-run
```

Then execute:

```bash
/usr/bin/time -v Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase all
```

The direct controller accepts `environment`, `parity`, `audit`, `cohort`, `annotations`, `qc`, `normalize`, `descriptive`, `pseudobulk`, `contrasts`, `pseudobulk_de`, `mast`, `mito_fraction`, `pathways`, `similarity`, `multiple_testing`, `sensitivity`, `power`, `validate`, `figures`, or `all`.

Recommended order within the first 12-hour allocation:

1. Vasculature parity and all nine lightweight audits.
2. Global cohort and annotation construction.
3. Raw-count QC and pseudobulk creation, prioritizing all nine RDS files.
4. Primary pseudobulk models.
5. Normalization one large RDS at a time.
6. MAST and expensive downstream work, continuing in later on-demand allocations if needed.

Minerva production is expected to complete the full analysis, but it is not required to finish in one 12-hour allocation. Resume the same Minerva production manifest in another on-demand allocation when tasks are making acceptable progress and fit within 192 GiB. Its completion manifest distinguishes `validated_complete`, `failed`, `not_started`, and `stopped_for_walltime`.

### 7.4 LSF fallback

LSF fallback is not a larger or scientifically richer analysis. It adds no nuclei, donors, cell types, contrasts, models, or final products beyond the full Minerva production manifest. Skip it when Minerva production completes and validates.

Activate LSF fallback only when a Minerva production task has a documented operational problem that is better handled by LSF, for example:

- It exceeds the 12-hour allocation or progresses too slowly for practical direct-node continuation.
- It exceeds the safe 192 GiB direct-node memory budget or is killed for out-of-memory use.
- It needs scheduler-managed arrays, per-task resource requests, dependency handling, or retries.
- The on-demand allocation is interrupted repeatedly and cannot complete a resumable task reliably.

LSF fallback imports the Minerva production completion manifest, reuses every validated output, and submits only `failed`, `stopped_for_walltime`, `not_started`, or invalid tasks approved for fallback. It uses the same `config/minerva_shared.yml` (~2-5 KB), `config/minerva_rds_manifest.tsv` (~2-5 KB), code revision, scientific parameters, seeds, and checksums as Minerva production. A task's execution backend may change; its scientific definition may not.

Only after the activation criteria above are met, create `config/phase3_lsf.yml` (~2-5 KB) and the necessary LSF wrappers from Section 24. Before submission, import and validate the Minerva production completion manifest (<5 MB). Reuse a Minerva production output only when its checksum, code revision, parameter checksum, schema, and validation status match the fallback release. Never rerun a valid task merely because LSF fallback was activated, and never run the direct controller and an LSF job for the same task simultaneously.

Create `scripts/reconcile_phase_handoff.R` (~10-20 KB) to classify every task as `reuse_validated`, `submit_missing`, `rerun_invalid`, or `blocked`. Run it before any LSF submission:

```bash
Rscript scripts/reconcile_phase_handoff.R \
  --config config/minerva_shared.yml \
  --minerva-production-manifest results/minerva_production/14_validation/minerva_production_completion_manifest.tsv \
  --execution-config config/phase3_lsf.yml \
  --dry-run
```

Write the reconciliation result to a fallback task manifest. Every LSF fallback wrapper must require that manifest and refuse to execute a task classified as `reuse_validated` or `blocked`. Array indices in the examples below must be replaced with the unresolved task IDs from that manifest; they are not instructions to submit the complete array.

A template job is:

```bash
#!/bin/bash
#BSUB -J mito_one_rds
#BSUB -P acc_YOURPROJECT
#BSUB -q YOUR_QUEUE
#BSUB -n 1
#BSUB -W 24:00
#BSUB -R "rusage[mem=64000]"
#BSUB -o results/minerva_production/logs/phase3/%J.out
#BSUB -e results/minerva_production/logs/phase3/%J.err

module purge
module load R/4.3.3

/usr/bin/time -v Rscript scripts/run_one_rds.R \
  --config config/minerva_shared.yml \
  --input "$INPUT_RDS"
```

Use measured Minerva production peaks to replace these initial requests:

| Input class | Example inputs and estimated disk size | Initial RAM request |
| --- | --- | ---: |
| Small, below ~2 GiB | Vasculature (~138 MiB), Immune (~616 MiB), OPCs (~1.1 GiB), Astrocytes (~1.6 GiB) | 32-64 GiB |
| Medium, ~5-6 GiB | Excitatory sets 1 and 3 (~5.7-5.8 GiB), Inhibitory (~5.2 GiB), Oligodendrocytes (~5.0 GiB) | ~96 GiB |
| Largest, ~9.8 GiB | Excitatory set 2 (~9.8 GiB) | ~128 GiB |

### 7.5 Promotion gates

**local-pilot-to-Minerva-production gate**

1. Vasculature audit finds all 13 mtDNA protein genes.
2. Cohort construction yields 276 global and 274 Vasculature donors.
3. Raw-count and pseudobulk conservation checks pass.
4. Normalized dimensions/count checksums remain unchanged.
5. Pilot pseudobulk and MAST schemas are fixed.
6. A clean local rerun is deterministic.
7. Configurations, annotations, package lockfile, and code revision are frozen.
8. Local-pilot and Minerva-production Vasculature dry-run graphs use identical shared script checksums, task types, argument names, schemas, and non-pilot scientific parameters; the local-pilot task IDs form a subset of Minerva production.

**Minerva production completion or optional LSF fallback activation gate**

1. Minerva Vasculature parity matches local pilot.
2. All nine RDS audits have terminal statuses.
3. The 192 GiB controller never exceeds its RAM reserve and records measured peaks.
4. Every Minerva production task is classified as validated, failed, not started, or stopped for wall time; no task is silently absent.
5. Direct-run statuses and outputs pass checksum/schema validation.
6. If all tasks are validated, Minerva production is final and LSF fallback is skipped.
7. If unresolved tasks remain, their failure mode justifies LSF rather than another ordinary Minerva production resume; LSF memory and wall-time requests are updated from measured values.
8. If LSF fallback is activated, its resume/import dry-run classifies every task as `reuse_validated`, `submit_missing`, `rerun_invalid`, or `blocked`, and submits only the unresolved subset.

Any scientific code or parameter change after either gate requires rerunning affected earlier checks.

### 7.6 Output roots and handoff

| Output root | Estimated size | Contents |
| --- | ---: | --- |
| `results/local_pilot/` | ~0.2-2 GB | Complete local Vasculature pilot and promotion report. |
| `results/minerva_production/` | ~40-100 GB | Shared atomic Minerva artifacts from Minerva production, plus separate LSF fallback logs/status manifests only if fallback is activated. |

Minerva production and an optional LSF fallback share validated artifacts but never share a live task. Deterministic task IDs and atomic rename-on-success prevent collisions. Source RDS files are immutable.

Sections 7-22 define numeric Phases 00-15 and cross-cutting analyses. In every concrete block below, the Minerva production command targets the complete production scope. The corresponding LSF fallback block is an optional LSF implementation of the same task and applies only to manifest rows not already validated in Minerva production. References in a LSF fallback block to “all nine objects,” “all contrasts,” or “final” describe the completeness requirement after combining reused Minerva production results with fallback results; they do not instruct rerunning all work through LSF.


### 7.7 Section 7 file-change inventory

This inventory covers repository files created or modified to implement Section 7. It excludes generated results and logs, and scientific-phase scripts owned by Sections 8-22.

#### Added: required for local pilot and Minerva production

| File | Purpose |
| --- | --- |
| `config/analysis_parameters.yml` | Shared scientific parameters used unchanged by both primary environments. |
| `config/local_pilot.yml` | Local-pilot resource limits and output root. |
| `config/local_pilot_execution.yml` | Local-pilot scope and execution settings. |
| `config/local_pilot_rds_manifest.tsv` | Local-pilot Vasculature input manifest. |
| `config/minerva_shared.yml` | Shared Minerva paths and environment settings. |
| `config/minerva_rds_manifest.tsv` | Minerva production manifest for all nine RDS inputs. |
| `config/minerva_production_execution.yml` | Minerva production on-demand resource and execution settings. |
| `renv.lock` | Frozen R package versions used for local validation and Minerva restoration. |
| `scripts/00_check_environment.R` | Verifies packages, paths, inputs, references, and writable outputs. |
| `.Rprofile` | Activates the project renv environment for R and Rscript sessions. |
| `.renvignore` | Restricts dependency discovery to executable project code, excluding data, results, documentation, and companion reference notebooks. |
| `renv/activate.R` | Standard renv project autoloader. |
| `renv/settings.json` | Pins the renv and Bioconductor environment settings. |
| `renv/.gitignore` | Excludes machine-specific renv libraries and caches while retaining portable environment metadata. |
| `scripts/run_one_rds.R` | Runs one manifest task with the same CLI and output schema in both primary environments. |
| `scripts/run_pipeline.R` | Builds, dry-runs, resumes, and executes the shared task graph. |

#### Added: only if optional LSF fallback is activated

| File | Purpose |
| --- | --- |
| `config/phase3_lsf.yml` | LSF resource settings derived from measured Minerva production failures. |
| `scripts/reconcile_phase_handoff.R` | Classifies Minerva production artifacts before any LSF fallback submission. |
| `jobs/00_check_environment.lsf` | Runs the environment check in the LSF environment. |

Other scientific LSF wrappers are listed with their owning phases in Sections 8-22 and summarized in Section 24.

#### Changed

| File | Change |
| --- | --- |
| `.gitignore` | Tracks portable code, configuration, and renv metadata while excluding local data, documentation, results, libraries, caches, and logs. |
| `docs/mitochondria_sex_apoe_research_plan.md` | Defines and maintains this execution contract and inventory. |

Section 7 does not modify existing scientific code. Once the new shared scripts pass the local pilot promotion gate, their code, CLI schemas, and scientific parameters are frozen for Minerva production; only environment-specific configuration values change.

#### Deleted

None. Source RDS files, metadata, references, and validated artifacts are never deleted by this workflow.

## 8. Phase 01: Audit Every Seurat Object

### High-level purpose

Before changing any expression data, establish what each Seurat object contains and whether it can support the planned analysis. The audit must record object class/version, assays and layers, dimensions, sparse-count validity, metadata fields, donor and cell-type coverage, feature names, mitochondrial genes, reductions, commands, and barcode agreement with the master metadata. It must also document whether an existing normalized `RNA` data layer is present. Its presence does not replace the professor-requested uniform normalization from raw counts.

Stop this phase if counts are absent, donor IDs cannot be joined, feature names cannot be resolved, mitochondrial genes are missing, or an object does not agree with the master cell metadata.

### Local pilot: audit Vasculature

- **Input:** `data/processed/Vasculature_cells.rds` (~139 MB), `data/processed/cell.meta.data.tsv` (~168 MB), and `config/local_pilot_rds_manifest.tsv` (~1 KB).
- **Output:** `results/local_pilot/01_audit/Vasculature_cells.audit.tsv` (<1 MB), `Vasculature_cells.features.tsv.gz` (~0.1-2 MB), `Vasculature_cells.cell_types.tsv` (<100 KB), `Vasculature_cells.donors.tsv` (<1 MB), and `Vasculature_cells.audit_status.tsv` (<100 KB).
- **What changes:** the script reads the object and calculates dimensions, classes, nonzero counts, integer-count validity, metadata completeness, donor/cell-type counts, mitochondrial-feature presence, barcode agreement, and donor-aggregated raw counts for XIST and UTY. It does not save or modify the RDS.
- **Required package load order:** the shared script loads `RcppAnnoy` and then Seurat before `readRDS()` so lazy S4 dispatch cannot trigger the Minerva `AnnoyAngular` module error. This operational initialization is identical in local pilot and Minerva production.
- **Create:** `scripts/01_audit_seurat_inputs.R` (~10-20 KB).
- **Execute:**

```bash
Rscript scripts/01_audit_seurat_inputs.R \
  --config config/local_pilot.yml \
  --manifest-row 1
```

- **Required output check:** 33,538 genes, 17,974 nuclei, 423 represented donors, 5 fine cell types, sparse integer-valued raw counts, unique barcodes, and all 13 mtDNA protein genes.

### Minerva production: audit Minerva inputs on demand

- **Input:** `config/minerva_rds_manifest.tsv` (~2-5 KB), nine project-relative `data/processed/*.rds` files (~34.9 GiB total), and `data/processed/cell.meta.data.tsv` (~168 MB).
- **Output:** audit/status bundles under `results/minerva_production/01_audit/` (~10-200 MB total).
- **What changes:** the direct controller launches isolated audit processes within the 160 GiB usable-RAM budget. No RDS is modified.
- **Manifest count semantics:** a numeric `expected_features`, `expected_cells`, `expected_donors`, or `expected_cell_types` value is pinned and must match exactly. `NA` means that count was unavailable before the first Minerva read; the audit records the observed value and does not fail solely because the expectation is unpinned. `NA` does not waive raw-count, metadata-completeness, barcode-agreement, cell-type-completeness, or mitochondrial-gene checks.
- **Create:** `scripts/run_pipeline.R` (~20-40 KB), using `scripts/01_audit_seurat_inputs.R` (~10-20 KB).
- **Minerva dry-run after local promotion and repository synchronization:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase audit \
  --dry-run

Rscript -e '
graph <- read.delim("results/minerva_production/00_environment/minerva_production_audit_task_graph.tsv")
print(graph[, c("stable_task_id", "rds_id", "scientific_script", "script_exists")])
stopifnot(
  nrow(graph) == 9L,
  length(unique(graph$rds_id)) == 9L,
  all(graph$scientific_script == "scripts/01_audit_seurat_inputs.R"),
  all(graph$script_exists)
)
'
```

Expected dry-run outcome: nine stable audit task IDs, one per enabled RDS manifest row, all using the promoted `scripts/01_audit_seurat_inputs.R` checksum and all reporting `script_exists = TRUE`. Stop without executing if the dry run exits nonzero or any check fails.

- **Execute on the Minerva on-demand node:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase audit

Rscript -e '
files <- list.files(
  "results/minerva_production/01_audit",
  pattern = "[.]audit_status[.]tsv$",
  full.names = TRUE
)
stopifnot(length(files) == 9L)
status <- do.call(rbind, lapply(files, read.delim, check.names = FALSE))
print(status[, c("stable_task_id", "source_rds", "peak_ram_gib", "validation_status")])
stopifnot(
  length(unique(status$stable_task_id)) == 9L,
  all(status$validation_status == "validated_complete")
)
'
```

If one row must be retried after synchronizing a corrected promoted script, run only that stable task through the shared wrapper so both its audit artifacts and controller status are replaced atomically. For `Excitatory_neurons_set1.rds`, the manifest identifier is `excitatory_set1`:

```bash
Rscript scripts/run_one_rds.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --rds-id excitatory_set1 \
  --task-mode audit \
  --script scripts/01_audit_seurat_inputs.R

sed -n "1,2p" results/minerva_production/01_audit/Excitatory_neurons_set1.audit.tsv
sed -n "1,2p" results/minerva_production/status/audit__excitatory_set1.tsv
```

When one or more RDS audits lack a nonempty donor inventory, a validated scientific status, or the current promoted audit-script checksum, first create the retry list and then use the terminal-safe loop below. The audit command is deliberately placed inside `if`; on failure, `break` stops only the loop and preserves the interactive shell. Never use `exit` in this loop because `exit` closes the Minerva terminal.

```bash
Rscript -e '
manifest <- read.delim("config/minerva_rds_manifest.tsv", check.names = FALSE)
enabled <- toupper(as.character(manifest$enabled)) %in% c("TRUE", "T", "1", "YES")
manifest <- manifest[enabled, , drop = FALSE]

audit_dir <- "results/minerva_production/01_audit"
script_output <- system2(
  "sha256sum",
  "scripts/01_audit_seurat_inputs.R",
  stdout = TRUE
)
current_script_sha <- strsplit(script_output[[1L]], "[[:space:]]+")[[1L]][[1L]]

for (i in seq_len(nrow(manifest))) {
  rds_id <- manifest$rds_id[[i]]
  base_name <- sub("[.][Rr][Dd][Ss]$", "", basename(manifest$input_rds[[i]]))
  audit_path <- file.path(audit_dir, paste0(base_name, ".audit.tsv"))
  donor_path <- file.path(audit_dir, paste0(base_name, ".donors.tsv"))
  status_path <- file.path(audit_dir, paste0(base_name, ".audit_status.tsv"))

  donor_ok <- file.exists(donor_path) && file.info(donor_path)$size > 0
  audit_ok <- FALSE
  if (file.exists(audit_path) && file.exists(status_path)) {
    audit <- tryCatch(read.delim(audit_path, check.names = FALSE), error = identity)
    status <- tryCatch(read.delim(status_path, check.names = FALSE), error = identity)
    audit_ok <- !inherits(audit, "error") && !inherits(status, "error") &&
      nrow(audit) == 1L && nrow(status) == 1L &&
      identical(audit$validation_status[[1L]], "validated_complete") &&
      identical(status$validation_status[[1L]], "validated_complete") &&
      identical(status$scientific_code_bundle_sha256[[1L]], current_script_sha)
  }

  if (!donor_ok || !audit_ok) cat(rds_id, "\n", sep = "")
}
' > /tmp/pending_phase01_rds_ids.txt

cat /tmp/pending_phase01_rds_ids.txt

while IFS= read -r rds_id; do
  rds_id="${rds_id//[[:space:]]/}"
  [ -n "$rds_id" ] || continue
  if [[ ! "$rds_id" =~ ^[a-z0-9_]+$ ]]; then
    echo "Invalid rds_id in retry list: $rds_id"
    break
  fi
  echo "Rerunning Phase 01 audit for: $rds_id"

  if Rscript scripts/run_one_rds.R \
    --config config/minerva_shared.yml \
    --execution-config config/minerva_production_execution.yml \
    --rds-id "$rds_id" \
    --task-mode audit \
    --script scripts/01_audit_seurat_inputs.R; then
    echo "Completed: $rds_id"
  else
    echo "Audit failed for $rds_id; the shell remains open."
    status_file="results/minerva_production/status/audit__${rds_id}.tsv"
    log_path=$(awk -F "\t" '
      NR == 1 { for (i = 1; i <= NF; i++) if ($i == "log_path") column = i }
      NR == 2 && column { print $column }
    ' "$status_file")
    echo "Inspect: $log_path"
    if [ -n "$log_path" ] && [ -f "$log_path" ]; then
      tail -n 100 "$log_path"
    else
      echo "No readable log_path was recorded; inspect $status_file."
    fi
    break
  fi
done < /tmp/pending_phase01_rds_ids.txt
```


Expected outcome: the wrapper exits zero, the four observed counts are present in the audit row, and both status rows say `validated_complete`. Unpinned `NA` expectations do not appear in `failed_checks`; any other failed check remains a real audit failure that must be investigated before Phase 02.

- **Required output check:** all nine audits finish with `validated_complete`; every audit records dimensions, donor and cell-type counts, sparse integer-valued raw counts, all measured mitochondrial genes, master-metadata agreement, peak RAM, code/config/manifest checksums, and exactly one terminal status. No source RDS is modified.

### LSF fallback: audit unresolved objects

- **Input:** `config/minerva_rds_manifest.tsv` (~2-5 KB), unresolved project-relative `data/processed/*.rds` files, `data/processed/cell.meta.data.tsv` (~168 MB), and the promoted audit script (~10-20 KB).
- **Output:** nine audit/status bundles under `results/minerva_production/01_audit/` (~10-200 MB total).
- **What changes:** one isolated direct-node child process or one LSF array task reads and validates one object. No source RDS is modified.
- **Create:** `jobs/02_audit_rds_array.lsf` (~2-5 KB), which calls `scripts/01_audit_seurat_inputs.R` (~10-20 KB).
- **Execute:**

```bash
bsub -J "audit_rds[1-9]" < jobs/02_audit_rds_array.lsf
```

- **Required output check:** exactly one terminal status exists for each fixed manifest row; expected dimensions and cell types are recorded; only failed objects are blocked from dependent work.

## 9. Phase 02: Build and Join the Clinical Cohort

### High-level purpose

Create one authoritative donor table before attaching clinical variables to cells. Normalize every `projid` to an eight-character string, require exactly one clinical row per donor, derive `sex`, `apoe_group`, `diagnosis`, age variables, PMI variables, and any validated batch fields, then join by key rather than row order. Every retained nucleus from one donor must receive identical donor-level values.

Reproduce the paper's sex check using donor-aggregated `XIST` and Y-linked genes such as `UTY`. The global checkpoint is 276 eligible donors. The local Vasculature object should contain 274 of them; eligible donors `20261901` and `11072071` are absent from that object.

Stop this phase if a retained donor has multiple clinical rows, any required clinical field is missing after the join, or the 276-donor checkpoint fails.

### Local pilot: build the global and Vasculature cohorts

- **Input:** the clinical CSV (~328 KB), `data/processed/cell.meta.data.tsv` (~168 MB), the validated local pilot audit summary, and `Vasculature_cells.donors.tsv` (<1 MB).
- **Output:** `results/local_pilot/02_cohort/global_cohort_276.tsv` (~50-200 KB), `vasculature_cohort_274.tsv` (~50-200 KB), `cohort_exclusion_flow.tsv` (<100 KB), `cohort_group_counts.tsv` (<100 KB), `sex_linked_expression_check.tsv` (<1 MB), `cohort_checks.tsv` (<100 KB), and `cohort_status.tsv` (<100 KB).
- **What changes:** derives analysis-ready donor fields, applies the prespecified exclusions, verifies the four reported sex-discordant donors using donor-aggregated XIST/UTY counts, and intersects the global cohort with Vasculature. Source clinical, cell metadata, and RDS files are unchanged.
- **Create:** `scripts/02_build_cohort.R` (~10-20 KB).
- **Execute through the shared controller:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase cohort

Rscript -e '
status <- read.delim("results/local_pilot/02_cohort/cohort_status.tsv")
checks <- read.delim("results/local_pilot/02_cohort/cohort_checks.tsv")
print(status[, c("global_donors", "audited_rds", "validation_status")])
print(checks[, c("check", "passed", "observed", "expected")])
stopifnot(
  status$validation_status[[1L]] == "validated_complete",
  all(checks$passed)
)
'
```

Expected outcome: the controller exits zero; the global cohort has 276 donors; the Vasculature cohort has 274 donors; the two absent eligible donors are `20261901` and `11072071`; all 12 diagnosis-by-sex-by-APOE cells are tabulated for both scopes; and the XIST/UTY check identifies exactly the four prespecified sex-discordant donors.

### Minerva production: build Minerva donor intersections

- **Input:** clinical CSV (~328 KB), master cell metadata (~168 MB), nine successful Minerva production audit summaries and nine matching `*.donors.tsv` inventories (~10-200 MB total), and `config/minerva_shared.yml` (~2-5 KB).
- **Output:** global cohort and per-RDS intersections under `results/minerva_production/02_cohort/` (~0.2-6 MB total).
- **What changes:** applies the frozen local pilot cohort logic once on the on-demand node and records donor coverage for every audited RDS.
- **Create:** the `cohort` mode in `scripts/run_pipeline.R` (~20-40 KB), calling `scripts/02_build_cohort.R` (~10-20 KB).
- **Execute only after the promoted Phase 01 script has produced all nine donor inventories:**

```bash
Rscript -e '
files <- list.files(
  "results/minerva_production/01_audit",
  pattern = "[.]donors[.]tsv$",
  full.names = TRUE
)
cat("Audit donor inventories:", length(files), "/ 9\n")
stopifnot(length(files) == 9L)
'

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase cohort
```

Expected outcome: the controller exits zero; `cohort_status.tsv` is `validated_complete`; the global cohort remains 276; every audited RDS has an eligible-donor intersection; and the scientific script, configuration, CLI schema, and output schema match the local-pilot task graph.

### LSF fallback: build unresolved donor intersections

- **Input:** clinical CSV (~328 KB), master cell metadata (~168 MB), nine successful audit summaries (~10-200 MB), and `config/minerva_shared.yml` (~2-5 KB).
- **Output:** `results/minerva_production/02_cohort/global_cohort_276.tsv` (~50-200 KB), per-RDS cohort/intersection tables (~0.1-5 MB total), exclusion flow (<100 KB), and status files (<1 MB total).
- **What changes:** applies the identical local pilot cohort logic and records which eligible donors occur in each RDS. No expression object is changed.
- **Create:** the cohort portion of `jobs/03_cohort_annotations.lsf` (~2-5 KB), calling `scripts/02_build_cohort.R` (~10-20 KB).
- **Execute:**

```bash
bsub < jobs/03_cohort_annotations.lsf
```

- **Required output check:** the global cohort remains 276; every RDS has a documented donor intersection and group-count table; cohort-definition checksums match local pilot.

## 10. Phase 03: Freeze Mitochondrial Gene and Pathway Annotations

### High-level purpose

Define the biological feature sets before looking at final group effects. Use GENCODE chromosome assignments for mtDNA genes, the 13 prespecified mtDNA-encoded protein genes, Human MitoCarta 3.0 for nuclear-encoded mitochondrial genes and pathway hierarchy, and the prespecified MSigDB/GO sets described in Section 6. Record aliases, duplicates, unmatched genes, measured status, tested status, source URL, source version, and checksums.

Use the same project-relative GENCODE path locally and on Minerva. Store it in the shared `config/analysis_parameters.yml` rather than in a environment-specific config:

```yaml
references:
  genome_build: GRCh38
  gencode_release: "44"
  gencode_gtf: data/reference/gencode/gencode.v44.basic.annotation.gtf.gz
  gencode_gtf_sha256: 3e52f82c63f8fd860bf632ccde10441c05751f4c342ad08c0a98e9e2700171a5
  mitocarta_source: data/reference/Human.MitoCarta3.0.xls
  mitocarta_sha256: e6ada0ae8dcd5447a5efb6f77c69a1c10b1ffa66521540a1e81b92c61e5505f2
  mitocarta_inventory_sheet: "A Human MitoCarta3.0"
  mitocarta_pathways_sheet: "C MitoPathways"
```

All execution environments must run from their Alzheimer project root so this relative path resolves to the local copy in local pilot and the Minerva copy in Minerva production and LSF fallback. Do not fall back to a user-home annotation path.

The feature annotation is shared across all execution environments. Minerva production and LSF fallback reuse the frozen MitoCarta source and scientific definitions promoted from local pilot; they may only add mappings for features absent from Vasculature.

### Local pilot: download and freeze annotations

- **Input:** `data/reference/gencode/gencode.v44.basic.annotation.gtf.gz` (~29 MB), official Human MitoCarta3.0 spreadsheet (expected ~1-10 MB), the audited 33,538-gene feature list (~0.1-2 MB), and `config/analysis_parameters.yml` (~5-10 KB).
- **Output:** immutable `data/reference/Human.MitoCarta3.0.xls` (~10 MB), plus `results/local_pilot/03_annotations/mtDNA_protein_genes.tsv` (<100 KB), `mitocarta_measured_genes.tsv` (~0.1-2 MB), `mitocarta_pathways.gmt` (~0.1-2 MB), `mitocarta_pathways.tsv` (~0.1-2 MB), `gene_alias_mapping.tsv` (~0.1-2 MB), `tested_gene_universe.tsv` (~1-10 MB), `gencode_gene_annotation.tsv` (~1-10 MB), `annotation_checks.tsv` (<100 KB), `annotation_manifest.tsv` (<100 KB), and `annotation_status.tsv` (<100 KB).
- **What changes:** verifies the existing project-relative GENCODE file, downloads one MitoCarta reference spreadsheet, and builds versioned mapping tables. It does not change an expression matrix.
- **Create:** `scripts/03_build_mito_annotations.R` (~10-20 KB); the GENCODE directory and file already exist.
- **Execute:**

```bash
GTF=data/reference/gencode/gencode.v44.basic.annotation.gtf.gz
test -r "$GTF"
gzip -t "$GTF"
sha256sum "$GTF"

mkdir -p data/reference
wget -O data/reference/Human.MitoCarta3.0.xls \
  https://personal.broadinstitute.org/scalvo/MitoCarta3.0/Human.MitoCarta3.0.xls

sha256sum data/reference/Human.MitoCarta3.0.xls

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase annotations

Rscript -e '
checks <- read.delim("results/local_pilot/03_annotations/annotation_checks.tsv")
status <- read.delim("results/local_pilot/03_annotations/annotation_status.tsv")
print(checks)
print(status)
stopifnot(all(checks$passed), identical(status$validation_status, "validated_complete"))
'
```

- **Required output check:** the GENCODE file is readable, passes `gzip -t`, and has SHA-256 `3e52f82c63f8fd860bf632ccde10441c05751f4c342ad08c0a98e9e2700171a5`; MitoCarta has SHA-256 `e6ada0ae8dcd5447a5efb6f77c69a1c10b1ffa66521540a1e81b92c61e5505f2`, 1,136 unique inventory symbols, and 154 pathway rows; all 13 expected mtDNA protein genes are measured; chromosome names are present; unmatched, aliased, and duplicate MitoCarta symbols are reported; every row of `annotation_checks.tsv` passes; and `annotation_status.tsv` reports `validated_complete`.

#### Completed local-pilot checkpoint and key results (2026-07-11)

Phase 03 completed locally with status `validated_complete`:

- All 11 validation checks passed.
- The script parsed 62,700 GENCODE gene records and one 33,538-feature Vasculature inventory.
- All 1,136 unique MitoCarta genes were processed; 1,134 were measured and 1,088 were test-eligible.
- The two explicit unmatched MitoCarta entries were `GPX1` and `RP11_469A15.2`.
- All 13 prespecified mtDNA protein genes were measured and test-eligible.
- The output contains 154 MitoCarta pathway definitions.
- Peak resident memory was approximately 0.76 GiB.

### Minerva production: map Minerva feature sets

- **Input:** frozen MitoCarta spreadsheet (~1-10 MB), Minerva project copy `data/reference/gencode/gencode.v44.basic.annotation.gtf.gz` (~29 MB), and audited feature lists (~10-200 MB total).
- **Output:** annotation tables under `results/minerva_production/03_annotations/` (~1-100 MB total).
- **What changes:** maps union and per-RDS features with the frozen local pilot definitions; expression matrices remain unchanged.
- **Create:** the `annotations` mode in `scripts/run_pipeline.R` (~20-40 KB), calling `scripts/03_build_mito_annotations.R` (~10-20 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase annotations

Rscript -e '
checks <- read.delim("results/minerva_production/03_annotations/annotation_checks.tsv")
status <- read.delim("results/minerva_production/03_annotations/annotation_status.tsv")
print(checks)
print(status)
stopifnot(all(checks$passed), identical(status$validation_status, "validated_complete"))
'
```

- **Required output check:** from the Minerva project root, both reference files are readable and their SHA-256 values match the local pilot; all rows in `annotation_checks.tsv` pass; `annotation_status.tsv` reports `validated_complete`; `feature_set_count` is 9; and every audited RDS has an explicit measured/tested universe. The successful local run does not create the nine Minerva feature mappings, so this command must still be run on the Minerva on-demand node after the promoted code and the ignored `data/reference/Human.MitoCarta3.0.xls` file have been synchronized separately.

### LSF fallback: map unresolved feature sets

- **Input:** frozen MitoCarta spreadsheet (~1-10 MB), project-relative `data/reference/gencode/gencode.v44.basic.annotation.gtf.gz` (~29 MB), nine audited feature lists (~10-200 MB total), and promoted annotation parameters (~5-10 KB).
- **Output:** LSF fallback annotation tables under `results/minerva_production/03_annotations/` (~1-100 MB total).
- **What changes:** maps the union and per-RDS feature sets while preserving the promoted gene-set definitions and reference checksums.
- **Create:** the annotation portion of `jobs/03_cohort_annotations.lsf` (~2-5 KB), calling `scripts/03_build_mito_annotations.R` (~10-20 KB).
- **Execute:** the same job submitted in Phase 02 runs cohort construction first and annotation mapping second:

```bash
bsub < jobs/03_cohort_annotations.lsf
```

- **Required output check:** the reference checksum matches local pilot; every RDS has a measured/tested gene universe; missing mitochondrial features are explicit rather than silently dropped.

## 11. Phase 04: Calculate Mitochondrial QC Without Removing the Target Signal

### High-level purpose

Compute mitochondrial QC metrics directly from raw counts before normalization:

- `nCount_RNA` and `nFeature_RNA`.
- `nCount_MT`, the sum over measured mtDNA-encoded genes.
- `percent.mt = 100 * nCount_MT / nCount_RNA`.
- Number of detected mtDNA genes per nucleus.
- MitoCarta UMI fraction as a distinct exploratory metric.

Summarize these metrics by fine cell type, donor, diagnosis, sex, and APOE group. The primary analysis retains nuclei already accepted by the original study. Flag extreme values with prespecified robust within-cell-type rules, inspect whether flags are group- or donor-dependent, and repeat key analyses after excluding flagged nuclei.

Do not automatically impose `percent.mt < 5`, and do not regress out `percent.mt` in the primary mitochondrial analysis. Either action could erase the biological signal being studied. Stop if mitochondrial fractions are all zero, one group systematically lacks mitochondrial features, or a few donors dominate the mitochondrial counts.

The shared Phase 04 implementation uses a five-scaled-MAD threshold within each fine cell type. It applies two-sided flags to `log1p(nCount_RNA)` and `log1p(nFeature_RNA)` and high-side flags to `percent.mt` and the MitoCarta UMI fraction. These flags are reported but do not remove nuclei. Donor-concentration reports warn when one donor contributes more than 25% or the top three donors contribute more than 50% of a cell type's mtDNA counts.

Source feature and nucleus dimensions are validated against the corresponding `validated_complete` Phase 01 audit. Large Minerva manifest rows may intentionally leave `expected_features` and `expected_cells` as `NA` until the audit establishes them; an `NA` is not treated as an expected dimension. When a manifest dimension is pinned, it must agree with the promoted audit before Phase 04 proceeds. The Phase 01 audit checksum is recorded in every Phase 04 status row.

### Local pilot: calculate Vasculature QC

- **Input:** raw Vasculature RDS (~139 MB), Vasculature cohort (~50-200 KB), and frozen mitochondrial annotations (~1-10 MB total).
- **Output:** `results/local_pilot/04_qc/vasculature_cell_qc.tsv.gz`, `vasculature_donor_celltype_qc.tsv`, `vasculature_qc_flags.tsv.gz`, `vasculature_group_missingness.tsv`, `vasculature_donor_concentration.tsv`, `vasculature_qc_thresholds.tsv`, `vasculature_qc_distributions.pdf`, `vasculature_qc_checks.tsv`, `vasculature_qc_manifest.tsv`, and `vasculature_qc_status.tsv` (~1.2 MB total in the completed pilot).
- **What changes:** calculates raw-count metrics and robust flags in separate output files. It does not remove cells or modify the RDS.
- **Create:** `scripts/04_mito_qc.R` (~20-40 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase qc

Rscript -e '
checks <- read.delim("results/local_pilot/04_qc/vasculature_qc_checks.tsv")
status <- read.delim("results/local_pilot/04_qc/vasculature_qc_status.tsv")
print(checks)
print(status)
stopifnot(all(checks$passed), identical(status$validation_status, "validated_complete"))
'
```

- **Required output check:** all 20 checks pass and status is `validated_complete`; mitochondrial counts are nonnegative; `percent.mt` and the MitoCarta UMI fraction are finite and between 0 and 100; source RDS dimensions and checksum are unchanged; every source nucleus has one QC row; the analytic cells reconcile to donor-cell-type summaries; and all 60 fine-cell-type-by-sex-by-APOE-by-diagnosis combinations plus all five cell-type donor-concentration summaries are reported, including combinations with zero nuclei.

#### Completed local-pilot checkpoint and key results (2026-07-11)

Phase 04 completed locally with status `validated_complete`:

- All 20 validation checks passed, and every generated artifact matched its manifest checksum and byte count.
- The source contained 17,974 nuclei; 12,904 nuclei from all 274 Vasculature analytic-cohort donors were represented across five fine cell types.
- Median analytic-cohort `percent.mt` was 1.024% (interquartile range 0.417%-2.306%; maximum 12.201%).
- Median analytic-cohort MitoCarta UMI fraction was 5.293% (interquartile range 4.376%-6.793%; maximum 19.182%).
- The five-scaled-MAD rules flagged 543 analytic nuclei (4.21%) without removing them; 154 nuclei (1.19%) had zero mtDNA counts.
- None of the five fine cell types crossed the 25% top-donor or 50% top-three-donor mtDNA-count warning thresholds.
- All 60 planned study-group rows were emitted. One row, male/APOE epsilon2/AD `Fib SLC4A4`, had zero nuclei and is explicitly retained as ineligible for later contrasts rather than omitted.
- The raw source RDS checksum was unchanged. Peak resident memory was approximately 1.88 GiB and the scientific script completed in approximately eight seconds.

### Minerva production: calculate QC on the on-demand node

- **Input:** successful raw RDS files (~34.9 GiB total), per-RDS cohorts (~0.1-5 MB), frozen annotations (~1-10 MB), and measured RAM estimates.
- **Output:** QC tables, figures, logs, and statuses under `results/minerva_production/04_qc/` (~0.1-2 GB total if all nine complete).
- **What changes:** the direct controller processes independent objects subject to the 160 GiB usable-RAM budget; source objects and primary cell sets remain unchanged.
- **Create:** the `qc` mode in `scripts/run_pipeline.R` (~20-40 KB), calling `scripts/04_mito_qc.R` (~10-20 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase qc

Rscript -e '
scientific_files <- list.files(
  "results/minerva_production/04_qc",
  pattern = "_qc_status[.]tsv$", full.names = TRUE
)
check_files <- list.files(
  "results/minerva_production/04_qc",
  pattern = "_qc_checks[.]tsv$", full.names = TRUE
)
controller_files <- list.files(
  "results/minerva_production/status",
  pattern = "^qc__.*[.]tsv$", full.names = TRUE
)
stopifnot(
  length(scientific_files) == 9L,
  length(check_files) == 9L,
  length(controller_files) == 9L
)
scientific <- do.call(rbind, lapply(scientific_files, read.delim))
checks <- do.call(rbind, lapply(check_files, read.delim))
controller <- do.call(rbind, lapply(controller_files, read.delim))
print(scientific[, c(
  "stable_task_id", "source_nuclei", "analytic_nuclei",
  "analytic_donors", "fine_cell_types", "peak_ram_gib",
  "validation_status"
)])
stopifnot(
  all(scientific$validation_status == "validated_complete"),
  all(checks$passed),
  all(controller$validation_status == "validated_complete"),
  all(controller$exit_code == 0L)
)
'
```

- **Required output check:** every launched RDS has a terminal controller status and a per-RDS scientific QC status; completed rows report `validated_complete`, all QC checks passing, explicit group-missingness and donor-concentration rows, and measured peak RAM. Unfinished rows are `stopped_for_walltime`, not silently absent. After all nine rows complete, `results/minerva_production/04_qc/` contains one validated output bundle per RDS.

### LSF fallback: calculate QC for unresolved RDS tasks

- **Input:** each successfully audited raw RDS (~34.9 GiB total), its cohort table (~50 KB-1 MB), frozen annotations (~1-10 MB), and shared QC parameters (~5-10 KB).
- **Output:** per-cell, donor-cell-type, flag, figure, and status bundles under `results/minerva_production/04_qc/` (~0.1-2 GB total).
- **What changes:** each array task computes the same local pilot QC fields independently for one RDS. No cell is removed from a primary source or working object.
- **Create:** the QC portion of `jobs/04_qc_normalize_rds_array.lsf` (~3-8 KB), calling `scripts/04_mito_qc.R` (~10-20 KB).
- **Execute:** submit by measured object-size tier:

```bash
bsub -J "qc_norm_small[1,5,7,9]" -R "rusage[mem=64000]" < jobs/04_qc_normalize_rds_array.lsf
bsub -J "qc_norm_medium[2,4,6,8]" -R "rusage[mem=96000]" < jobs/04_qc_normalize_rds_array.lsf
bsub -J "qc_norm_large[3]" -R "rusage[mem=128000]" < jobs/04_qc_normalize_rds_array.lsf
```

- **Required output check:** one QC status exists for every successful audit row; mitochondrial metrics pass range checks; missingness and extreme-donor reports cover every fine cell type.

## 12. Phase 05: Attach Metadata and Normalize With Seurat `NormalizeData`

### High-level purpose

Use the professor-requested Seurat `NormalizeData` result for cell-level summaries and the secondary MAST analysis. For each object independently, set the RNA assay and run `LogNormalize` with scale factor 10,000:

```r
DefaultAssay(obj) <- "RNA"
obj <- NormalizeData(
  object = obj,
  assay = "RNA",
  normalization.method = "LogNormalize",
  scale.factor = 10000,
  verbose = TRUE
)
```

Before normalization, attach keyed donor metadata and separately calculated QC fields. Preserve the source RDS and raw `counts` layer. Verify that sampled output entries equal `log1p(count / cell_total * 10000)`, that dimensions do not change, and that the saved object reloads.

The normalized working object retains every source nucleus and uses `cohort_included` to identify the analytic subset; normalization does not perform cohort or QC filtering. Phase 02 contributes diagnosis, sex, APOE, age, and PMI fields, and Phase 04 contributes raw-count mitochondrial metrics and non-exclusionary QC flags. Phase 05 records exact serialized raw-count matrix hashes before normalization, after normalization, and after output reload.

For large Minerva matrices, validation-sample size calculations must coerce `nrow` and `ncol` to double precision before multiplication; multiplying two R integer dimensions can overflow even though only 500 random entries are sampled. Tabular prerequisites are read with `integer64 = "double"` while donor/barcode identifiers remain explicitly character, so the optional `bit64` print package is not required and integer64 columns do not emit misleading display warnings.

Some source RDS objects were serialized with an older Seurat class layout. Under the locked Seurat 5.5.1 and SeuratObject 5.4.0 environment, an old `Assay` can lack the newly required `assay.orig` slot and fail during `NormalizeData()` with `invalid class "Assay" object`. The shared Phase 05 script therefore calls `SeuratObject::UpdateSeuratObject()` immediately after `readRDS()`, requires the upgraded in-memory object to pass `validObject()`, and records the source object version, upgraded object version, and active Seurat package versions in its status. Only the normalized working copy is upgraded; the source RDS and its checksum remain unchanged.

The Minerva `rl_readline_state` line can still appear at R startup and is unrelated to this schema failure. Messages about an assay or dimensional reduction changing to the same named class are expected while `UpdateSeuratObject()` reconstructs legacy slots; the terminal object-validation and Phase 05 checks must still pass.

`ScaleData` is not normalization and is not an input to count-based pseudobulk analysis. Integrated expression must not be used for disease differential expression. A separately named SCTransform branch may be used only as a sensitivity analysis; it must not overwrite the primary result.

### Local pilot: normalize Vasculature

- **Input:** raw Vasculature RDS (~139 MB), Vasculature cohort (~50-200 KB), cell QC (~2-20 MB), and shared normalization settings (~5-10 KB).
- **Output:** `results/local_pilot/05_normalized/Vasculature_cells.normalized.rds` (~139 MB), `Vasculature_cells.normalization_formula_samples.tsv` (<1 MB), `Vasculature_cells.normalization_validation.tsv` (<100 KB), `Vasculature_cells.normalization_manifest.tsv` (<100 KB), and `Vasculature_cells.normalization_status.tsv` (<100 KB).
- **What changes:** creates a working copy with derived donor/QC metadata and a recomputed RNA `data` layer. Raw `counts`, cells, genes, and the source RDS remain unchanged.
- **Create:** `scripts/05_normalize_and_attach_metadata.R` (~20-30 KB), reusing tested logic from `scripts/05_normalize_seurat_rds.R` (~3.9 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase normalize

Rscript -e '
validation <- read.delim(
  "results/local_pilot/05_normalized/Vasculature_cells.normalization_validation.tsv"
)
status <- read.delim(
  "results/local_pilot/05_normalized/Vasculature_cells.normalization_status.tsv"
)
print(validation)
print(status)
stopifnot(
  nrow(validation) == 20L,
  all(validation$passed),
  identical(status$validation_status, "validated_complete")
)
'
```

- **Required output check:** all 20 validation checks pass and status is `validated_complete`; dimensions and exact serialized raw-count hash are unchanged in memory and after reload; 1,000 sampled normalized entries match the configured formula within `1e-8`; cohort and QC joins are complete and persist after reload; the source RDS checksum is unchanged; and every output artifact matches the normalization manifest.

#### Completed local-pilot checkpoint and key results (revalidated 2026-07-12)

Phase 05 completed locally with status `validated_complete`:

- All 20 validation checks passed, and every generated artifact matched its manifest checksum and byte count.
- The normalized working object retained all 33,538 features and 17,974 source nuclei; 12,904 nuclei from all 274 Vasculature analytic-cohort donors were marked `cohort_included`.
- The RNA assay contains preserved `counts` and recomputed `data` layers, with `RNA` retained as the default assay.
- The raw-count matrix SHA-256 remained `932dbad43871749e37a014550e978251da3d69a050bafb7a68368e240912e9db` before normalization, after normalization, and after output reload.
- All 1,000 deterministic formula samples passed exactly: 517 sampled nonzero entries and 483 zero entries had maximum absolute error `0` both in memory and after reload.
- The saved object retained 28 metadata fields, including Phase 02 cohort variables and Phase 04 mitochondrial metrics and QC flags.
- The source RDS checksum remained unchanged. The normalized object was 145,127,693 bytes, peak resident memory was approximately 2.73 GiB, and the scientific script completed in approximately 40 seconds.
- The compatibility rerun upgraded the working object from Seurat object version 3.1.5 to 5.4.0 under Seurat 5.5.1/SeuratObject 5.4.0; all 20 checks still passed with zero formula error.

### Minerva production: normalize within 192 GiB

- **Input:** successful raw RDS files (~34.9 GiB total), cohort/QC files (~0.1-200 MB per RDS), and frozen normalization settings (~5-10 KB).
- **Output:** normalized objects under `results/minerva_production/05_normalized/` (~35-70 GB total if complete), plus validations/logs (~1-20 MB).
- **What changes:** runs one large object alone and admits multiple small objects only when their estimated peaks plus 32 GiB reserve fit within 192 GiB.
- **Create:** the `normalize` mode in `scripts/run_pipeline.R` (~20-40 KB), calling `scripts/05_normalize_and_attach_metadata.R` (~10-20 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase normalize

Rscript -e '
scientific_files <- list.files(
  "results/minerva_production/05_normalized",
  pattern = "[.]normalization_status[.]tsv$", full.names = TRUE
)
validation_files <- list.files(
  "results/minerva_production/05_normalized",
  pattern = "[.]normalization_validation[.]tsv$", full.names = TRUE
)
controller_files <- list.files(
  "results/minerva_production/status",
  pattern = "^normalize__.*[.]tsv$", full.names = TRUE
)
stopifnot(
  length(scientific_files) == 9L,
  length(validation_files) == 9L,
  length(controller_files) == 9L
)
scientific <- do.call(rbind, lapply(scientific_files, read.delim))
validation <- do.call(rbind, lapply(validation_files, read.delim))
controller <- do.call(rbind, lapply(controller_files, read.delim))
print(scientific[, c(
  "stable_task_id", "features", "nuclei", "analytic_nuclei",
  "analytic_donors", "max_formula_error", "peak_ram_gib",
  "validation_status"
)])
stopifnot(
  all(scientific$validation_status == "validated_complete"),
  all(validation$passed),
  all(controller$validation_status == "validated_complete"),
  all(controller$exit_code == 0L),
  length(unique(scientific$scientific_code_bundle_sha256)) == 1L
)
'
```

#### Retry after the legacy `Assay` schema error

The `assay.orig` error requires the promoted shared-script update; reinstalling Seurat is not the remedy when the locked package versions are already correct.

1. Wait for the original controller to finish, or stop it before synchronizing code. Confirm that no normalization process remains:

```bash
pgrep -af 'run_pipeline[.]R.*--phase normalize|05_normalize_and_attach_metadata[.]R'
```

Expected outcome: no matching process is printed. Do not replace the script while an older controller is still launching tasks.

2. Commit and synchronize the locally validated revision to Minerva, start a prepared Minerva shell as described in Section 7.3, and verify the promoted script:

```bash
sha256sum scripts/05_normalize_and_attach_metadata.R
```

Expected SHA-256: `fe393fca3b30ffad5b896d4097829caee46f0cb6945504ca962e9c890b1fa03e`.

3. Confirm the locked package pair in the activated project library:

```bash
Rscript -e '
cat("Seurat:", as.character(packageVersion("Seurat")), "\n")
cat("SeuratObject:", as.character(packageVersion("SeuratObject")), "\n")
'
```

Expected outcome: Seurat `5.5.1` and SeuratObject `5.4.0`. The `rl_readline_state` startup warning may still appear.

4. Dry-run and then rerun all nine Phase 05 tasks with the promoted script:

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase normalize --dry-run

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase normalize
```

Expected dry-run outcome: nine `normalize:<rds_id>` rows, `script_exists = TRUE`, and the promoted script checksum in the task graph. Rerun all nine rather than mixing outputs from old and new script checksums. Expected execution outcome: the final validation block above finds nine scientific statuses and nine controller statuses, every status is `validated_complete`, all validation checks pass, and all scientific statuses contain one shared script checksum.

- **Required output check:** all nine scientific and controller statuses report `validated_complete` under one script checksum; every validation row passes; each object reloads; dimensions and exact raw-count hashes match its source; metadata/formula assertions pass; and peak RAM is recorded. The direct controller processes objects sequentially, so the largest object runs alone.

### LSF fallback: normalize unresolved objects

- **Input:** each successful raw RDS (~34.9 GiB total), its cohort/QC files (~0.1-200 MB per RDS), and promoted normalization parameters (~5-10 KB).
- **Output:** nine validated working objects under `results/minerva_production/05_normalized/` (~35-70 GB total), plus validation/status files (~1-20 MB total).
- **What changes:** the same array tasks used in Phase 04 attach metadata and rebuild the RNA `data` layer one object at a time. Source RDS files and counts remain unchanged.
- **Create:** the normalization portion of `jobs/04_qc_normalize_rds_array.lsf` (~3-8 KB), calling `scripts/05_normalize_and_attach_metadata.R` (~10-20 KB).
- **Execute:** use the three Phase 04 size-tier submissions; the job runs normalization only after that row's QC succeeds.
- **Required output check:** every successful audit row has either one readable normalized object or an explicit failure; raw-count checksums and dimensions match its source; resource use is recorded.

## 13. Phase 06: Descriptive Analysis Before Hypothesis Tests

### High-level purpose

Before fitting disease models, describe the available biological replication. For each fine cell type, report nuclei and donors overall; donors and median nuclei in each of the 12 diagnosis-by-sex-by-APOE cells; raw library size; detected genes; `percent.mt`; mitochondrial counts; detection of all 13 mtDNA protein genes; MitoCarta coverage; and donors failing sample-size rules.

Use at least 20 nuclei per donor-cell-type pseudobulk sample for the main analysis and 50 nuclei as a sensitivity threshold. Require at least five eligible donors on each side of a formal contrast; smaller comparisons are descriptive only. Do not select cell types because preliminary disease p-values look interesting.

Phase 06 uses the compact Phase 04 cell- and donor-level tables for coverage and eligibility. To provide the prespecified per-cell-type detection of all 13 mtDNA protein genes and MitoCarta coverage, the shared script reads one source RDS at a time and accesses only the required raw-count feature subsets. It never combines large RDS objects, modifies an expression object, filters a nucleus, or fits a hypothesis test.

### Local pilot: summarize the five vascular cell types

- **Input:** raw Vasculature RDS (~139 MB), Phase 01 audit, Phase 02 cohort, Phase 03 mitochondrial annotations, Phase 04 cell/donor QC, and the Phase 05 validation status.
- **Output:** `results/local_pilot/06_descriptive/vasculature_group_coverage.tsv`, `vasculature_contrast_coverage.tsv`, `vasculature_sample_eligibility.tsv`, `vasculature_mito_detection.tsv`, `vasculature_mitocarta_coverage.tsv`, `vasculature_descriptive_figures.pdf`, `vasculature_descriptive_checks.tsv`, `vasculature_descriptive_manifest.tsv`, and `vasculature_descriptive_status.tsv` (~364 KB total in the completed pilot).
- **What changes:** aggregates existing metadata, QC fields, and selected mitochondrial raw-count rows into donor-aware summaries. It does not filter expression data, alter an RDS, or fit hypothesis tests.
- **Create:** `scripts/06_summarize_celltypes.R` (~30 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase descriptive

Rscript -e '
checks <- read.delim(
  "results/local_pilot/06_descriptive/vasculature_descriptive_checks.tsv"
)
status <- read.delim(
  "results/local_pilot/06_descriptive/vasculature_descriptive_status.tsv"
)
print(checks)
print(status)
stopifnot(
  nrow(checks) == 20L,
  all(checks$passed),
  identical(status$validation_status, "validated_complete")
)
'
```

- **Required output check:** all 20 checks pass and status is `validated_complete`; all five fine cell types have all 12 planned study-group rows; the 60 group rows, 30 AD-versus-NCI coverage rows, 65 cell-type-by-mtDNA-gene rows, and five MitoCarta coverage rows reconcile to the cohort/QC/raw-count inputs; eligibility uses the configured 20/50-nucleus and five-donor thresholds; and the source RDS checksum is unchanged.

#### Completed local-pilot checkpoint and key results (2026-07-12)

Phase 06 completed locally with status `validated_complete`:

- All 20 validation checks passed, and all seven generated artifacts matched their manifest checksums and byte counts.
- The summaries cover five fine cell types, 12,904 analytic nuclei, all 274 Vasculature analytic-cohort donors, and 1,053 observed donor-cell-type samples.
- At the primary 20-nucleus threshold, 196 donor-cell-type samples (18.6%) were eligible; 37 (3.5%) were eligible at the 50-nucleus sensitivity threshold.
- Of the 30 possible cell-type-by-sex-by-APOE AD-versus-NCI strata, three met the primary requirement of at least five eligible donors on both sides: female epsilon3/epsilon3 `End`, male epsilon3/epsilon3 `End`, and female epsilon3/epsilon3 `Per`. None met the 50-nucleus sensitivity threshold on both sides.
- All 60 cell-type-by-sex-by-APOE-by-diagnosis group rows were emitted. Male/epsilon2/AD `Fib SLC4A4` was the one zero-nucleus group and remains explicitly ineligible rather than omitted.
- All 13 mtDNA protein genes were measured in every cell type. Across cell-type/gene combinations, nucleus detection ranged from 1.02% for the sparsest `MT-ND6` combination to 94.78% for the strongest `MT-CO3` combination.
- Of 1,136 MitoCarta inventory genes, 1,134 were measured and 1,088 were test-eligible. Depending on cell type, 1,041-1,074 measured genes were detected in analytic nuclei (91.8%-94.7% of measured genes).
- The source RDS checksum was unchanged. Peak resident memory was approximately 1.62 GiB and the finalized scientific script completed in approximately seven seconds.

### Minerva production: summarize all Minerva inputs

- **Input:** all nine raw RDS files, validated Phase 01-05 bundles, and frozen eligibility/mitochondrial definitions.
- **Output:** per-RDS descriptive tables and figures under `results/minerva_production/06_descriptive/` (~10-200 MB total if all nine complete).
- **What changes:** processes one RDS at a time, combining compact coverage tables and reading only selected mitochondrial raw-count rows; no large objects are merged or modified.
- **Create:** the `descriptive` mode in `scripts/run_pipeline.R` (~20-40 KB), calling `scripts/06_summarize_celltypes.R` (~30 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase descriptive --dry-run

Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase descriptive

Rscript -e '
scientific_files <- list.files(
  "results/minerva_production/06_descriptive",
  pattern = "_descriptive_status[.]tsv$", full.names = TRUE
)
check_files <- list.files(
  "results/minerva_production/06_descriptive",
  pattern = "_descriptive_checks[.]tsv$", full.names = TRUE
)
controller_files <- list.files(
  "results/minerva_production/status",
  pattern = "^descriptive__.*[.]tsv$", full.names = TRUE
)
stopifnot(
  length(scientific_files) == 9L,
  length(check_files) == 9L,
  length(controller_files) == 9L
)
scientific <- do.call(rbind, lapply(scientific_files, read.delim))
checks <- do.call(rbind, lapply(check_files, read.delim))
controller <- do.call(rbind, lapply(controller_files, read.delim))
print(scientific[, c(
  "stable_task_id", "fine_cell_types", "analytic_nuclei",
  "analytic_donors", "donor_celltype_samples",
  "primary_eligible_samples", "primary_eligible_contrasts",
  "peak_ram_gib", "validation_status"
)])
stopifnot(
  sum(scientific$fine_cell_types) == 54L,
  all(scientific$validation_status == "validated_complete"),
  all(checks$passed),
  all(controller$validation_status == "validated_complete"),
  all(controller$exit_code == 0L),
  length(unique(scientific$scientific_code_bundle_sha256)) == 1L
)
'
```

- **Expected dry-run outcome:** nine stable `descriptive:<rds_id>` tasks, all using `scripts/06_summarize_celltypes.R` with `script_exists = TRUE` and one promoted script checksum.
- **Required output check:** all nine scientific/controller statuses are `validated_complete` under one script checksum; all checks pass; the status rows total 54 fine cell types; every cell type has 12 group rows, 6 AD-versus-NCI coverage rows, 13 mtDNA-gene rows, and one MitoCarta coverage row; donor/nucleus totals reconcile; and all missing or underpowered strata remain explicit.

### LSF fallback: regenerate summaries affected by fallback work

- **Input:** nine audit bundles (~10-200 MB), per-RDS cohorts (~0.1-5 MB), and QC summaries (~0.1-2 GB).
- **Output:** combined and per-RDS descriptive tables under `results/minerva_production/06_descriptive/` (~10-200 MB) and figures (~20-200 MB total).
- **What changes:** combines compact summaries across objects, retaining source-RDS provenance; it does not merge large cell-level matrices.
- **Create:** `jobs/05_descriptive.lsf` (~2-5 KB), calling `scripts/06_summarize_celltypes.R` (~30 KB).
- **Execute:**

```bash
bsub < jobs/05_descriptive.lsf
```

- **Required output check:** all 54 expected fine cell types are represented or explicitly reported missing; donor totals reconcile with per-RDS cohorts; low-coverage groups are visibly flagged.

## 14. Phase 07: Primary Donor-Level Pseudobulk Analysis

### High-level purpose

The 276 donors are the independent biological samples; nuclei are nested observations. The primary analysis therefore sums **raw counts** by `projid` and `cell_type_high_resolution` and uses an edgeR quasi-likelihood count model. Never aggregate normalized values for edgeR or DESeq2.

For each pseudobulk column, retain donor, diagnosis, sex, APOE group, age, PMI, validated batch, nuclei count, total UMI count, and mitochondrial QC summaries. Use `filterByExpr` or a comparably justified filter, while keeping the 13 mtDNA genes in descriptive output even if they lack enough information for formal testing.

Use a 12-level diagnosis-sex-APOE group plus covariates:

```r
group <- interaction(diagnosis, sex, apoe_group, drop = TRUE)
design <- model.matrix(
  ~ 0 + group + age_scaled + pmi_scaled,
  data = sample_metadata
)
```

Test AD minus NCI in female and male epsilon2, epsilon3/epsilon3, and epsilon4 groups. Also test: the female-minus-male difference in AD effect within each APOE group; epsilon2-minus-epsilon3/epsilon3 and epsilon4-minus-epsilon3/epsilon3 differences within each sex; and a global test of AD-effect heterogeneity across the six sex-APOE groups. A significant result in one subgroup and a nonsignificant result in another is not itself an interaction. Report effect size, confidence interval, raw p-value, FDR, donor count, nucleus count, and detection rate for every estimable test; retain explicit statuses for ineligible tests.

### Local pilot: construct Vasculature pseudobulk counts

- **Input:** raw Vasculature RDS (~139 MB), Vasculature cohort (~50-200 KB), cell QC (~2-20 MB), and minimum-cell rules (~5-10 KB).
- **Output:** per-RDS count bundle, sample table, exact-conservation checks, artifact manifest, and scientific status under `results/local_pilot/07_pseudobulk/` (~19.9 MB in the completed pilot).
- **What changes:** sums raw UMI counts by normalized donor ID and fine cell type and adds sample metadata/eligibility flags. Normalized values and source counts are not changed.
- **Create:** shared `scripts/07_make_pseudobulk.R` (~20 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase pseudobulk --dry-run

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase pseudobulk

Rscript -e '
status <- read.delim(
  "results/local_pilot/07_pseudobulk/Vasculature_cells.pseudobulk_status.tsv"
)
checks <- read.delim(
  "results/local_pilot/07_pseudobulk/Vasculature_cells.pseudobulk_count_conservation.tsv"
)
print(status)
print(checks)
stopifnot(
  identical(status$validation_status, "validated_complete"),
  nrow(checks) == 11L,
  all(checks$passed)
)
'
```

- **Expected dry-run outcome:** exactly one `pseudobulk:vasculature` task, using `scripts/07_make_pseudobulk.R` with `script_exists = TRUE`.
- **Required output check:** all 11 checks pass; gene-wise and total UMI sums are conserved exactly for included cells; one sample-metadata row exists per pseudobulk column; the source raw-count hash matches Phase 05.

### Local pilot: create the pilot contrast manifest

- **Input:** pseudobulk sample metadata (~0.1-5 MB), five vascular cell types, six sex-APOE AD-versus-NCI definitions, interaction definitions, and donor-count rules (~5-10 KB).
- **Output:** `results/local_pilot/07_contrasts/local_pilot_contrast_manifest.tsv`, checks, artifact manifest, and scientific status (<100 KB total).
- **What changes:** enumerates every planned test and its donor counts, including tests that are ineligible. It does not analyze expression.
- **Create:** shared `scripts/07_build_contrast_manifest.R` (~15 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase contrasts --dry-run

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase contrasts

Rscript -e '
manifest <- read.delim(
  "results/local_pilot/07_contrasts/local_pilot_contrast_manifest.tsv"
)
checks <- read.delim(
  "results/local_pilot/07_contrasts/local_pilot_contrast_manifest_checks.tsv"
)
status <- read.delim(
  "results/local_pilot/07_contrasts/local_pilot_contrast_manifest_status.tsv"
)
stopifnot(
  nrow(manifest) == 70L,
  sum(manifest$paper_matched) == 30L,
  sum(manifest$eligibility_status == "eligible") == 4L,
  all(checks$passed),
  identical(status$validation_status, "validated_complete")
)
'
```

- **Expected dry-run outcome:** exactly one `global:contrasts` task, using `scripts/07_build_contrast_manifest.R` with `script_exists = TRUE`.
- **Required output check:** all five vascular cell types have six paper-matched AD-versus-NCI rows, three sex-interaction rows, four APOE-interaction rows, and one global-heterogeneity row; every row is explicitly `eligible` or `ineligible`.

### Local pilot: fit edgeR models

- **Input:** pseudobulk counts (~20-200 MB), sample metadata (~0.1-5 MB), contrast manifest (<1 MB), and tested-gene universes (~0.1-2 MB).
- **Output:** result table, model diagnostics, per-contrast statuses, checks, artifact manifest, and scientific status under `results/local_pilot/07_pseudobulk_de/` (~1.8 MB total in the completed pilot).
- **What changes:** filters testable genes, calculates TMM factors, fits edgeR quasi-likelihood models, evaluates contrasts, and applies declared FDR procedures. Saved raw pseudobulk counts remain unchanged.
- **Create:** shared `scripts/07_run_pseudobulk_de.R` (~25 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase pseudobulk_de --dry-run

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase pseudobulk_de

Rscript -e '
status <- read.delim(
  "results/local_pilot/07_pseudobulk_de/vasculature.pseudobulk_de_status.tsv"
)
checks <- read.delim(
  "results/local_pilot/07_pseudobulk_de/vasculature.pseudobulk_de_checks.tsv"
)
contrasts <- read.delim(
  "results/local_pilot/07_pseudobulk_de/vasculature.pseudobulk_contrast_status.tsv"
)
stopifnot(
  identical(status$validation_status, "validated_complete"),
  all(checks$passed),
  sum(contrasts$terminal_status == "validated_complete") == 4L,
  sum(contrasts$terminal_status == "ineligible") == 66L,
  !any(contrasts$terminal_status == "failed")
)
'
```

- **Expected dry-run outcome:** exactly one `pseudobulk_de:vasculature` task, using `scripts/07_run_pseudobulk_de.R` with `script_exists = TRUE`.
- **Required output check:** every eligible row has results; every failed/ineligible row has an explicit terminal status; result keys are unique; p-values/FDR values are valid; result rows include donor counts, effect sizes, 95% confidence intervals for one-degree-of-freedom tests, detection rates, and source provenance.

#### Completed local-pilot checkpoint and key results (2026-07-12)

Phase 07 completed locally with all scientific and controller statuses `validated_complete`:

- Pseudobulk aggregation retained 12,904 analytic-cohort nuclei from 274 donors and five vascular cell types, producing 1,053 donor-cell-type samples; 196 samples met the primary threshold of at least 20 nuclei.
- All 38,053,722 included-cell UMIs were conserved exactly. No gene had a nonzero count difference, and the source raw-count SHA-256 matched the Phase 05 hash `932dbad43871749e37a014550e978251da3d69a050bafb7a68368e240912e9db`.
- The frozen manifest contains 70 rows: 30 paper-matched AD-versus-NCI tests and 40 prespecified interaction/omnibus tests. Four were eligible and 66 were explicitly ineligible under the five-donors-per-required-group rule.
- Eligible tests were endothelial female e33 AD versus NCI (13 versus 16 donors), endothelial male e33 AD versus NCI (10 versus 21), the endothelial female-minus-male e33 AD-effect interaction, and pericyte female e33 AD versus NCI (9 versus 9).
- Both fitted cell-type models were full rank. `filterByExpr` retained 5,935 endothelial genes and 5,199 pericyte genes. All four eligible contrasts completed, producing 23,004 unique `(cell type, contrast, gene)` rows; no contrast failed.
- Three genes passed within-contrast BH FDR <0.05, all in endothelial male e33 AD versus NCI: `PLPP1` (log2FC 1.541, 95% CI 0.915 to 2.166, FDR 0.0149), `HBA1` (log2FC 4.745, 95% CI 2.833 to 6.658, FDR 0.0149), and `HBA2` (log2FC 4.197, 95% CI 2.446 to 5.947, FDR 0.0178). No interaction passed FDR <0.05.
- Eligibility matched Phase 06 exactly, result keys were unique, all artifact byte counts/checksums matched, and peak RAM was approximately 2.40 GiB for aggregation and 0.49 GiB for edgeR fitting.

These discoveries are nonfinal local-pilot results from only the vascular RDS. They validate the workflow but are not production biological conclusions; the hemoglobin-gene signals in particular require review for vascular/blood-content effects and confirmation in Minerva production and sensitivity analyses.

### Minerva production: construct Minerva pseudobulk data

- **Input:** successful raw RDS files (~34.9 GiB total), cohorts (~0.1-5 MB), QC summaries (~0.1-2 GB), and minimum-cell rules.
- **Output:** pseudobulk counts/sample tables under `results/minerva_production/07_pseudobulk/` (~0.5-5 GB total if complete).
- **What changes:** sums raw counts in isolated RDS processes; this does not require normalized objects and is prioritized within the 12-hour allocation.
- **Create:** the `pseudobulk` mode in `scripts/run_pipeline.R` (~20-40 KB), calling `scripts/07_make_pseudobulk.R` (~10-20 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk --dry-run

Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase pseudobulk

Rscript -e '
scientific_files <- list.files(
  "results/minerva_production/07_pseudobulk",
  pattern = "[.]pseudobulk_status[.]tsv$", full.names = TRUE
)
check_files <- list.files(
  "results/minerva_production/07_pseudobulk",
  pattern = "[.]pseudobulk_count_conservation[.]tsv$", full.names = TRUE
)
controller_files <- list.files(
  "results/minerva_production/status",
  pattern = "^pseudobulk__.*[.]tsv$", full.names = TRUE
)
stopifnot(length(scientific_files) == 9L, length(check_files) == 9L, length(controller_files) == 9L)
scientific <- do.call(rbind, lapply(scientific_files, read.delim))
checks <- do.call(rbind, lapply(check_files, read.delim))
controller <- do.call(rbind, lapply(controller_files, read.delim))
stopifnot(
  all(scientific$validation_status == "validated_complete"),
  all(checks$passed),
  all(controller$validation_status == "validated_complete"),
  all(controller$exit_code == 0L),
  sum(scientific$fine_cell_types) == 54L
)
'
```

- **Expected dry-run outcome:** nine stable `pseudobulk:<rds_id>` tasks, all with `script_exists = TRUE` and the promoted `scripts/07_make_pseudobulk.R` checksum.
- **Required output check:** all nine scientific/controller statuses are `validated_complete`; every conservation check passes; the statuses total 54 fine cell types; one sample row exists per pseudobulk column. Do not run `contrasts` if any RDS is missing or failed.

### LSF fallback: construct unresolved pseudobulk data

- **Input:** successful raw RDS files (~34.9 GiB total), per-RDS cohorts (~0.1-5 MB), QC summaries (~0.1-2 GB), and shared minimum-cell rules (~5-10 KB).
- **Output:** per-RDS count objects and sample tables under `results/minerva_production/07_pseudobulk/` (~0.5-5 GB total), plus conservation reports/statuses (~1-50 MB).
- **What changes:** one array task sums raw counts by donor and fine cell type for one RDS and marks sample eligibility.
- **Create:** `jobs/05_pseudobulk_rds_array.lsf` (~2-5 KB), calling `scripts/07_make_pseudobulk.R` (~10-20 KB).
- **Execute:**

```bash
bsub -J "pseudobulk_rds[1-9]" < jobs/05_pseudobulk_rds_array.lsf
```

- **Required output check:** count conservation passes for every RDS; all 54 expected fine cell types are represented or explicitly reported missing.

### Minerva production: create the Minerva contrast manifest

- **Input:** completed pseudobulk sample tables (~1-50 MB), 54 expected cell types, six paper-matched contrasts, interactions, and donor rules.
- **Output:** `results/minerva_production/07_contrasts/minerva_production_contrast_manifest.tsv` (~0.1-5 MB).
- **What changes:** enumerates tests for available sample tables and records tasks blocked by incomplete pseudobulk inputs.
- **Create:** the `contrasts` mode in `scripts/run_pipeline.R` (~20-40 KB), calling `scripts/07_build_contrast_manifest.R` (~8-15 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase contrasts --dry-run

Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase contrasts

Rscript -e '
manifest <- read.delim(
  "results/minerva_production/07_contrasts/minerva_production_contrast_manifest.tsv"
)
checks <- read.delim(
  "results/minerva_production/07_contrasts/minerva_production_contrast_manifest_checks.tsv"
)
status <- read.delim(
  "results/minerva_production/07_contrasts/minerva_production_contrast_manifest_status.tsv"
)
stopifnot(
  nrow(manifest) == 756L,
  sum(manifest$paper_matched) == 324L,
  all(manifest$eligibility_status %in% c("eligible", "ineligible")),
  all(checks$passed),
  identical(status$validation_status, "validated_complete"),
  status$analysis_units == 54L
)
'
```

- **Expected dry-run outcome:** one `global:contrasts` task with `script_exists = TRUE` and the promoted `scripts/07_build_contrast_manifest.R` checksum.
- **Required output check:** 756 total rows exist for 54 cell types: 324 paper-matched rows plus 432 prespecified interaction/omnibus rows. Every row is `eligible` or `ineligible`, all checks pass, and no test disappears.

### LSF fallback: rebuild the contrast manifest if affected

- **Input:** all pseudobulk sample metadata (~1-50 MB), 54 fine cell types, six paper-matched contrasts, interactions, and donor eligibility rules (~5-10 KB).
- **Output:** `results/minerva_production/07_contrasts/minerva_production_contrast_manifest.tsv` (~0.1-5 MB), containing all 324 paper-matched rows plus interactions and statuses.
- **What changes:** merges compact sample metadata and enumerates tests. No expression matrix is modified.
- **Create:** `jobs/06_build_contrast_manifest.lsf` (~2-5 KB), calling `scripts/07_build_contrast_manifest.R` (~8-15 KB).
- **Execute:**

```bash
bsub < jobs/06_build_contrast_manifest.lsf
```

- **Required output check:** exactly 324 paper-matched rows exist before eligibility filtering; every row records donor counts and source-RDS provenance.

### Minerva production: run all eligible primary models

- **Input:** completed pseudobulk bundles (~0.5-5 GB), Minerva contrast manifest (~0.1-5 MB), and tested-gene universes (~1-10 MB).
- **Output:** primary results/statuses under `results/minerva_production/07_pseudobulk_de/` (~100 MB-2 GB if complete).
- **What changes:** runs independent edgeR contrasts under the direct controller's contrast concurrency and wall-time guard.
- **Create:** the `pseudobulk_de` mode in `scripts/run_pipeline.R` (~20-40 KB), calling `scripts/07_run_pseudobulk_de.R` (~15-30 KB).
- **MKL requirement:** first run the complete new-session block in Section 7.3. The Minerva `R/4.3.3` build requires the matching Intel Parallel Studio XE 2019 MKL link group to be preloaded for edgeR fitting. Do not load a newer standalone MKL module.
- **Mandatory preflight on every new node/session:** verify the preload libraries, then complete a representative edgeR fit. A small `crossprod()` test is insufficient because it does not exercise the failing fitting path.

```bash
for library in \
  "$MKL_LIB/libmkl_gf_lp64.so" \
  "$MKL_LIB/libmkl_gnu_thread.so" \
  "$MKL_LIB/libmkl_core.so" \
  "$MKL_LIB/libmkl_avx2.so"
do
  test -r "$library" || {
    echo "Required MKL library is missing or unreadable: $library" >&2
    exit 1
  }
done

LD_PRELOAD="$MKL_PRELOAD" Rscript -e '
suppressPackageStartupMessages(library(edgeR))

set.seed(123)
counts <- matrix(
  rnbinom(2000L * 120L, mu = 20, size = 5),
  nrow = 2000L
)
group <- factor(rep(paste0("group", 1:6), each = 20))
design <- model.matrix(~ 0 + group)

y <- DGEList(counts)
keep <- filterByExpr(y, design)
y <- y[keep, , keep.lib.sizes = FALSE]
y <- calcNormFactors(y)
y <- estimateDisp(y, design, robust = TRUE)
fit <- glmQLFit(y, design, robust = TRUE)

stopifnot(nrow(fit$counts) > 0)
cat("Representative edgeR/MKL test succeeded\n")
'
```

The preflight must end with `Representative edgeR/MKL test succeeded`. The `rl_readline_state` warning is non-blocking, but any `Intel MKL FATAL ERROR`, missing library, undefined symbol, rank error, or nonzero exit is blocking. Do not start or resume Phase 07.3 until the preflight passes.

- **Execute after the preflight passes, in the same shell:**

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk_de --dry-run

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase pseudobulk_de

LD_PRELOAD="$MKL_PRELOAD" Rscript -e '
scientific_files <- list.files(
  "results/minerva_production/07_pseudobulk_de",
  pattern = "[.]pseudobulk_de_status[.]tsv$", full.names = TRUE
)
check_files <- list.files(
  "results/minerva_production/07_pseudobulk_de",
  pattern = "[.]pseudobulk_de_checks[.]tsv$", full.names = TRUE
)
contrast_files <- list.files(
  "results/minerva_production/07_pseudobulk_de",
  pattern = "[.]pseudobulk_contrast_status[.]tsv$", full.names = TRUE
)
controller_files <- list.files(
  "results/minerva_production/status",
  pattern = "^pseudobulk_de__.*[.]tsv$", full.names = TRUE
)
stopifnot(length(scientific_files) == 9L, length(check_files) == 9L,
          length(contrast_files) == 9L, length(controller_files) == 9L)
scientific <- do.call(rbind, lapply(scientific_files, read.delim))
checks <- do.call(rbind, lapply(check_files, read.delim))
contrasts <- do.call(rbind, lapply(contrast_files, read.delim))
controller <- do.call(rbind, lapply(controller_files, read.delim))
stopifnot(
  all(scientific$validation_status == "validated_complete"),
  all(checks$passed),
  all(controller$validation_status == "validated_complete"),
  all(controller$exit_code == 0L),
  nrow(contrasts) == 756L,
  !any(contrasts$terminal_status == "failed"),
  all(contrasts$terminal_status %in% c("validated_complete", "ineligible"))
)
cat("Phase 07.3 Minerva production validated successfully\n")
'
```

- **Expected dry-run outcome:** nine stable `pseudobulk_de:<rds_id>` tasks, all with `script_exists = TRUE` and the promoted `scripts/07_run_pseudobulk_de.R` checksum.
- **Required output check:** all nine scientific/controller statuses are `validated_complete`; all 756 manifest rows have one terminal status; every eligible contrast completed, every underpowered contrast is explicitly `ineligible`, no contrast failed, and all per-RDS result keys/p-value/FDR checks pass. Unresolved work remains in the Minerva production resume manifest unless its failure mode meets the optional LSF fallback activation criteria.

### LSF fallback: run unresolved primary models

- **Input:** per-RDS pseudobulk counts (~0.5-5 GB total), sample metadata (~1-50 MB), full contrast manifest (~0.1-5 MB), and tested-gene universes (~1-10 MB).
- **Output:** one result/status bundle per manifest row under `results/minerva_production/07_pseudobulk_de/` (~100 MB-2 GB total).
- **What changes:** performs in-memory TMM normalization and edgeR modeling and writes compact results. Saved counts remain unchanged.
- **Create:** `jobs/07_pseudobulk_de_array.lsf` (~3-8 KB) and `jobs/submit_phase3_lsf.sh` (~5-15 KB), calling `scripts/07_run_pseudobulk_de.R` (~15-30 KB).
- **Execute:**

```bash
bash jobs/submit_phase3_lsf.sh --phase pseudobulk_de
```

- **Required output check:** one terminal status exists per manifest row; there are no duplicate `(cell_type, contrast, gene)` keys; failed rows can be rerun by manifest ID.

## 15. Phase 08: Paper-Comparable Cell-Level MAST Analysis

### MAST summary

In this phase, **MAST** means **Model-based Analysis of Single-cell Transcriptomics**, not the MEME Suite's similarly named motif-search tool. MAST is a differential-expression method designed for single-cell or single-nucleus RNA-seq data, where many gene-by-cell measurements are zero. Its two-part hurdle model tests both whether a gene is detected in a cell and, when detected, how strongly it is expressed. It can incorporate covariates such as total RNA count, age at death, and postmortem interval. Here, MAST provides a paper-comparable secondary analysis; donor-level pseudobulk remains primary because including cell-level covariates does not account for the non-independence of multiple nuclei from the same donor.

### High-level purpose

Run a secondary Seurat/MAST branch closely matching Yu et al. and the companion `Section_F_DEG_pipeline.Rmd`. Within one sex-APOE subset and fine cell type, compare AD with NCI using normalized RNA data, `min.pct = 0.10`, `logfc.threshold = 0`, and the available paper-like covariates:

```r
FindMarkers(
  object = obj,
  ident.1 = "AD",
  ident.2 = "NCI",
  group.by = "diagnosis",
  subset.ident = target_cell_type,
  test.use = "MAST",
  min.pct = 0.10,
  logfc.threshold = 0,
  latent.vars = c("nCount_RNA", "age_death_numeric", "pmi")
)
```

Confirm exact Seurat v5 assay/layer behavior before execution. Apply the paper-like reporting rule after testing: BH-adjusted p-value <0.05, absolute fold change >1.3 (absolute log2 fold change >~0.3785), and detection in at least 10% of cells in either group.

This branch supports paper comparability but remains secondary because ordinary cell-level latent variables do not make nuclei from one donor independent. Compare MAST with pseudobulk by effect direction, magnitude, rank, and support.

### Local pilot: run Vasculature MAST

- **Input:** normalized Vasculature RDS (~145 MB), frozen Phase 07 contrast manifest/sample eligibility, Phase 07 pseudobulk results, and shared MAST parameters.
- **Output:** result table, model diagnostics, per-contrast statuses, checks, artifact manifest, and scientific status under `results/local_pilot/08_mast/` (~660 KB total in the completed pilot).
- **What changes:** subsets cells in memory and fits MAST; it does not modify the normalized object. The paper-style branch fits only paper-matched AD-versus-NCI rows. Interaction/omnibus rows remain primary pseudobulk tests and receive explicit `not_applicable` MAST statuses.
- **Create:** shared `scripts/08_run_mast.R` (~30 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase mast --dry-run

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase mast

Rscript -e '
status <- read.delim(
  "results/local_pilot/08_mast/vasculature.mast_de_status.tsv"
)
checks <- read.delim(
  "results/local_pilot/08_mast/vasculature.mast_de_checks.tsv"
)
contrasts <- read.delim(
  "results/local_pilot/08_mast/vasculature.mast_contrast_status.tsv"
)
stopifnot(
  identical(status$validation_status, "validated_complete"),
  nrow(checks) == 10L,
  all(checks$passed),
  nrow(contrasts) == 70L,
  sum(contrasts$terminal_status == "validated_complete") == 3L,
  sum(contrasts$terminal_status == "ineligible") == 27L,
  sum(contrasts$terminal_status == "not_applicable") == 40L,
  !any(contrasts$terminal_status == "failed")
)
'
```

- **Expected dry-run outcome:** exactly one `mast:vasculature` task, using `scripts/08_run_mast.R` with `script_exists = TRUE`.
- **Required output check:** all 10 checks pass; all 70 manifest rows have one terminal status; the three eligible paper-matched rows complete; donor and cell counts match Phase 07; result keys are unique; p-values/FDR and the 10% detection filter are valid; the normalized RDS checksum is unchanged.

#### Completed local-pilot checkpoint and key results (2026-07-12)

Phase 08 completed locally with scientific and controller status `validated_complete`:

- Seurat 5.5.1 with MAST 1.28.0 fitted the three eligible paper-style AD-versus-NCI contrasts. The latent variables were `nCount_RNA`, `age_death_scaled`, and `pmi_scaled`; scaling age and PMI changes their coefficient units but not the adjusted diagnosis test.
- Endothelial female e33 compared 495 AD nuclei from 13 donors with 522 NCI nuclei from 16 donors and tested 4,847 genes. Endothelial male e33 compared 261 AD nuclei from 10 donors with 896 NCI nuclei from 21 donors and tested 5,228 genes. Pericyte female e33 compared 405 AD nuclei from 9 donors with 266 NCI nuclei from 9 donors and tested 4,883 genes.
- The combined output contains 14,958 unique `(cell type, contrast, gene)` rows. The paper reporting rule identified 73 DEGs: 27 in endothelial female e33, 39 in endothelial male e33, and 7 in pericyte female e33.
- Direction/magnitude agreement with donor-level pseudobulk was broadly positive: Spearman log2FC correlations were 0.752, 0.807, and 0.819 for endothelial female e33, endothelial male e33, and pericyte female e33, respectively.
- `PLPP1` was the only gene significant by both methods: endothelial male e33 MAST log2FC 1.154 and FDR 0.0148 versus pseudobulk log2FC 1.541 and FDR 0.0149, with concordant direction. The pseudobulk `HBA1` and `HBA2` signals were not in the MAST tested set after the 10% detection filter.
- All artifact sizes/checksums matched, the normalized-object SHA-256 remained unchanged, peak RAM was approximately 2.59 GiB, and the scientific script completed in approximately 121 seconds.

The 73 MAST calls are secondary, nonfinal local-pilot results. MAST treats nuclei as cell-level observations and the listed latent variables do not account for within-donor correlation; the much larger MAST call set relative to the three pseudobulk discoveries must not be interpreted as stronger donor-level evidence.

### Minerva production: run all eligible MAST work

- **Input:** completed normalized RDS files (~35-70 GB if all available), contrast manifest (~0.1-5 MB), and MAST parameters.
- **Output:** MAST bundles under `results/minerva_production/08_mast/` (~0.1-5 GB if complete).
- **What changes:** runs at most one MAST task per source RDS at a time; large source objects run without another large RDS process.
- **Create:** the `mast` mode in `scripts/run_pipeline.R` (~20-40 KB), calling `scripts/08_run_mast.R` (~15-30 KB).
- **Prerequisite:** Phase 07.3 must finish and pass its complete Minerva validation before Phase 08 starts. Do not run the two phases concurrently.
- **MKL runtime:** use the Section 7.3 Intel Parallel Studio XE 2019 setup and the same scoped `LD_PRELOAD` for MAST. Do not mix this R environment with a newer standalone MKL module. In the same initialized shell, confirm or restore these variables:

```bash
cd /sc/arion/work/zhuane01/alzheimer

export MKLROOT=/hpc/packages/minerva-centos7/intel/parallel_studio_xe_2019/compilers_and_libraries/linux/mkl
export MKL_LIB="$MKLROOT/lib/intel64_lin"
export MKL_PRELOAD="$MKL_LIB/libmkl_gf_lp64.so:$MKL_LIB/libmkl_gnu_thread.so:$MKL_LIB/libmkl_core.so"

export LD_LIBRARY_PATH="$MKL_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LD_RUN_PATH="$LD_LIBRARY_PATH"
export MKL_ENABLE_INSTRUCTIONS=AVX2
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

unset LD_DEBUG LD_DEBUG_OUTPUT
```

- **Execute:** first inspect the dry-run graph, then run MAST only if all nine scripts exist.

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast --dry-run

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast

LD_PRELOAD="$MKL_PRELOAD" Rscript -e '
scientific_files <- list.files(
  "results/minerva_production/08_mast",
  pattern = "[.]mast_de_status[.]tsv$",
  full.names = TRUE
)
check_files <- list.files(
  "results/minerva_production/08_mast",
  pattern = "[.]mast_de_checks[.]tsv$",
  full.names = TRUE
)
contrast_files <- list.files(
  "results/minerva_production/08_mast",
  pattern = "[.]mast_contrast_status[.]tsv$",
  full.names = TRUE
)
controller_files <- list.files(
  "results/minerva_production/status",
  pattern = "^mast__.*[.]tsv$",
  full.names = TRUE
)

stopifnot(
  length(scientific_files) == 9L,
  length(check_files) == 9L,
  length(contrast_files) == 9L,
  length(controller_files) == 9L
)

scientific <- do.call(rbind, lapply(scientific_files, read.delim))
checks <- do.call(rbind, lapply(check_files, read.delim))
contrasts <- do.call(rbind, lapply(contrast_files, read.delim))
controller <- do.call(rbind, lapply(controller_files, read.delim))

print(table(contrasts$terminal_status))

stopifnot(
  all(scientific$validation_status == "validated_complete"),
  all(checks$passed),
  all(controller$validation_status == "validated_complete"),
  all(controller$exit_code == 0L),
  sum(scientific$manifest_rows) == 756L,
  nrow(contrasts) == 756L,
  !any(contrasts$terminal_status == "failed"),
  all(contrasts$terminal_status %in%
      c("validated_complete", "ineligible", "not_applicable"))
)

cat("Phase 08 Minerva production validated successfully\n")
'
```

#### Multi-node Phase 08 execution and recovery by RDS

The nine Phase 08 RDS tasks are scientifically independent. They read shared normalized objects, the frozen contrast manifest, and Phase 07 bundles without modifying them; each task writes RDS-specific MAST artifacts, a controller status, and a log. To reduce wall time, run one distinct RDS ID per Minerva compute node. Every node must use the same Git revision, configs, manifest, renv library, Section 7.3 module setup, and MKL preload. Never run the same RDS ID concurrently on two nodes.

Valid production RDS IDs are:

```text
astrocytes
excitatory_set1
excitatory_set2
excitatory_set3
immune
inhibitory
opcs
oligodendrocytes
vasculature
```

On each node, choose exactly one ID and run:

```bash
RDS_ID=astrocytes  # replace with the one RDS assigned to this node

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast \
  --rds-id "$RDS_ID" \
  --dry-run

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast \
  --rds-id "$RDS_ID"
```

The per-RDS dry run writes a collision-free graph named `results/minerva_production/00_environment/minerva_production_mast_<rds_id>_task_graph.tsv` and must show exactly one task with `script_exists = TRUE`.

Because `resume: true` is set in `config/minerva_production_execution.yml`, a completed MAST task is skipped only if all of the following still match:

- controller task ID, source RDS, execution identity, zero exit code, and `validated_complete` status;
- scientific-script, scientific-configuration, and RDS-manifest checksums;
- the scientific MAST status and zero failed contrasts;
- normalized-RDS, contrast-manifest, pseudobulk-sample, and pseudobulk-DE checksums; and
- existence, byte count, SHA-256, and `validated_complete` status of every recorded MAST artifact.

A valid skip prints `Resume: skipping validated task mast:<rds_id> because code, inputs, statuses, and artifact checksums match.` If a node goes down, start a replacement node, repeat the Section 7.3/MKL setup, and rerun the same per-RDS command. A fully validated task is skipped; an incomplete, failed, missing, changed, or checksum-mismatched task runs again. Partial files are never treated as completed merely because they exist.

To intentionally rerun a validated RDS, add `--force`:

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast \
  --rds-id "$RDS_ID" \
  --force
```

After all nine node commands finish, run the combined Phase 08 validation block above once from any initialized node. It must find nine scientific statuses, nine check tables, nine contrast-status tables, and nine controller statuses covering all 756 manifest rows.

- **Full-stage expected dry-run outcome:** nine stable `mast:<rds_id>` tasks, all with `script_exists = TRUE` and the promoted `scripts/08_run_mast.R` checksum.
- **Required output check:** all nine scientific/controller statuses are `validated_complete`; all 756 manifest rows have one terminal status; every eligible paper-matched row completed, every underpowered paper row is `ineligible`, all 432 interaction/omnibus rows are `not_applicable`, no row failed, and donor/cell counts and normalized-object checksums are recorded. Resume unfinished contrasts in Minerva production unless they meet the optional LSF fallback activation criteria.

### LSF fallback: run unresolved MAST rows

- **Input:** nine normalized RDS files (~35-70 GB total), full contrast manifest (~0.1-5 MB), tested-gene definitions (~1-10 MB), and MAST parameters (~5-10 KB).
- **Output:** one result/status bundle per eligible row under `results/minerva_production/08_mast/` (~0.1-5 GB total).
- **What changes:** each array task loads the required object, subsets one comparison in memory, and fits MAST. Normalized RDS files remain unchanged.
- **Create:** `jobs/08_mast_array.lsf` (~3-8 KB), called through `jobs/submit_phase3_lsf.sh` (~5-15 KB) and using `scripts/08_run_mast.R` (~15-30 KB).
- **Execute:**

```bash
bash jobs/submit_phase3_lsf.sh --phase mast
```

- **Required output check:** every eligible row reaches a terminal status; cell and donor counts are both recorded; failures can be rerun by manifest row ID.

## 16. Phase 09: Mitochondrial Read Fraction, Pathways, and Mitonuclear Balance

### High-level purpose

Treat mitochondrial read fraction as a separate donor-level outcome. For each donor and fine cell type, retain mitochondrial UMI counts and total UMI counts and use an overdispersed proportion model such as beta-binomial, or a carefully validated weighted transformed-proportion model. Test the same diagnosis, sex, APOE, covariates, and interactions as the expression analysis. Always report mitochondrial counts, total counts, and their ratio together because a higher ratio can reflect more mitochondrial transcription, less nuclear/cytoplasmic RNA, damage, apoptosis, or technical handling.

For expression pathways, rank all tested genes by a signed statistic. Test frozen MitoCarta pathways first and MSigDB C2:CP pathways for Yu comparability. Also perform a complementary over-representation analysis using all genes tested in that contrast as background.

Construct prespecified donor-level summaries for mtDNA-encoded OXPHOS, nuclear-encoded OXPHOS, complexes I-V, mitochondrial ribosome, and mitochondrial translation. Do not derive a score from genes selected as significant in these donors and then test that score in the same donors.

### Local pilot: run local mitochondrial downstream models

- **Input:** donor-cell-type QC (~0.1-2 MB), pseudobulk results (~10-100 MB), MAST results (~10-200 MB), pseudobulk counts (~20-200 MB), contrast manifest (<1 MB), and frozen pathways (~0.1-2 MB).
- **Output:** `results/local_pilot/10_downstream/mito_fraction_models.tsv` (~0.1-10 MB), `pathway_results.tsv` (~0.1-20 MB), `mitonuclear_balance.tsv` (~0.1-10 MB), diagnostics (~0.1-10 MB), and representative figures (~5-50 MB).
- **What changes:** fits donor-aware proportion models, ranks existing DE results, tests external gene sets, and calculates frozen mitonuclear summaries. It does not alter upstream counts or model results.
- **Create:** `scripts/09_run_mito_fraction_models.R` (~10-20 KB) and `scripts/09_run_mito_pathways.R` (~15-30 KB).
- **Execute:**

```bash
Rscript scripts/09_run_mito_fraction_models.R --config config/local_pilot.yml
Rscript scripts/09_run_mito_pathways.R --config config/local_pilot.yml
```

- **Required output check:** every modeled ratio has numerator and denominator fields; pathway backgrounds match tested genes; external gene-set checksums are present; all output is labeled `local_pilot`.

### Minerva production: run all mitochondrial downstream models

- **Input:** completed QC/pseudobulk/MAST bundles (~0.2-7 GB) and frozen pathways (~0.1-2 MB).
- **Output:** read-fraction, pathway, and mitonuclear results under `results/minerva_production/09_downstream/` (~10-500 MB when complete).
- **What changes:** runs all compact-result analyses after their dependencies complete. Blocked analyses remain in the Minerva production resume manifest unless the blocking task is moved to optional LSF fallback under the activation criteria.
- **Create:** `mito_fraction` and `pathways` modes in `scripts/run_pipeline.R` (~20-40 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase mito_fraction
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase pathways
```

- **Required output check:** only dependency-complete contrasts are analyzed; every blocked or incomplete item has an explicit status.

### LSF fallback: run affected mitochondrial downstream models

- **Input:** complete QC summaries (~0.1-2 GB), pseudobulk/MAST results (~0.2-7 GB), pseudobulk counts (~0.5-5 GB), full contrast manifest (~0.1-5 MB), and frozen pathways (~0.1-2 MB).
- **Output:** read-fraction, pathway, and mitonuclear results under `results/minerva_production/09_downstream/` (~10-500 MB total), plus diagnostics/statuses (~1-100 MB).
- **What changes:** merges validated compact summaries and fits the final models across all eligible fine cell types and contrasts. Upstream bundles remain immutable.
- **Create:** read-fraction and pathway calls in `jobs/09_downstream.lsf` (~3-8 KB), invoking `scripts/09_run_mito_fraction_models.R` (~10-20 KB) and `scripts/09_run_mito_pathways.R` (~15-30 KB).
- **Execute:**

```bash
bsub < jobs/09_downstream.lsf
```

- **Required output check:** all estimable manifest rows are represented; multiple-testing families are recorded; numerator/denominator and gene-universe checks pass.

## 17. Phase 10: Zhang-Yu Similarity Analysis Focused on Mitochondria

### High-level purpose

Recreate the paper's ternary coding for every gene and contrast: `+1` for significantly upregulated in AD, `0` for not significantly changed, and `-1` for significantly downregulated. Calculate female-versus-male similarity within APOE groups and APOE-group similarity within sex. Apply the method first to all tested genes, then extract mtDNA/MitoCarta genes. A pathway-level signed-effect analogue is an extension and must be labeled as such.

Use 10,000 permutations and empirical FDR in the final analysis. Validate the implementation with hand-calculated identical, one-sided, and opposite-direction examples. Repeat using paper-like MAST calls and primary pseudobulk calls so conclusions do not depend entirely on one thresholding method.

### Local pilot: validate similarity logic

- **Input:** Vasculature pseudobulk results (~10-100 MB), MAST results (~10-200 MB), pilot manifest (<1 MB), and mitochondrial annotations/pathways (~1-10 MB).
- **Output:** `results/local_pilot/10_downstream/similarity_smoke.tsv` (<5 MB), toy-example checks (<1 MB), permutation diagnostics (<5 MB), and status (<100 KB).
- **What changes:** creates ternary calls and runs a reduced, clearly nonfinal smoke-test permutation set. Upstream DE results are unchanged.
- **Create:** `scripts/10_similarity_analysis.R` (~15-30 KB).
- **Execute:**

```bash
Rscript scripts/10_similarity_analysis.R \
  --config config/local_pilot.yml
```

- **Required output check:** toy examples match hand calculations; pseudobulk and MAST branches are separate; outputs are labeled `local_pilot` and `nonfinal_smoke_test`.

### Minerva production: run final similarity analysis

- **Input:** completed pseudobulk/MAST results (~0.2-7 GB), Minerva contrast manifest (~0.1-5 MB), and annotations (~1-10 MB).
- **Output:** similarity outputs under `results/minerva_production/10_downstream/` (~10-500 MB).
- **What changes:** runs the final 10,000-permutation tasks for every eligible comparison after validation; smoke-test settings remain confined to local pilot.
- **Create:** the `similarity` mode in `scripts/run_pipeline.R` (~20-40 KB), calling `scripts/10_similarity_analysis.R` (~15-30 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase similarity
```

- **Required output check:** smoke and final outputs are unambiguously labeled; seeds and completed permutation counts are recorded.

### LSF fallback: run affected similarity tasks

- **Input:** complete pseudobulk and MAST result bundles (~0.2-7 GB), full contrast manifest (~0.1-5 MB), and frozen annotations/pathways (~1-10 MB).
- **Output:** final gene-level similarity results under `results/minerva_production/10_downstream/` (~10-500 MB).
- **What changes:** creates final ternary calls, runs 10,000 seeded permutations, computes empirical FDR, and extracts mitochondrial subsets.
- **Create:** the similarity call in `jobs/09_downstream.lsf` (~3-8 KB), invoking the same `scripts/10_similarity_analysis.R` (~15-30 KB) with full permutation limits selected by the production config.
- **Execute:**

```bash
bsub < jobs/09_downstream.lsf
```

- **Required output check:** 10,000 permutations and seeds are recorded; all planned comparisons have terminal statuses; formula/version metadata are included.

## 18. Phase 11: Cross-Cutting Multiple Testing and Decision Rules

Define testing families before opening final results:

1. Correct the 13 mtDNA-gene tests across all tested cell-type and contrast combinations as one prespecified family, while also showing within-contrast FDR for comparability.
2. Correct MitoCarta gene tests across measured genes and all planned contrasts.
3. Correct pathway tests across all tested pathways, cell types, and planned contrasts.
4. Report genome-wide FDR in the standard way for each contrast and provide a global sensitivity correction across contrasts.

Use FDR below 0.05 as the statistical threshold. For Yu-comparable DEG labels, also require absolute fold change above 1.3. Do not discard smaller effects from forest plots or ranked pathway analysis.

The within-contrast corrections remain in their owning Phase 07-10 outputs. The across-cell-type and across-contrast corrections require all independent per-RDS jobs to finish, so they are applied by one read-only global aggregation step. This avoids race conditions and prevents an early-finishing RDS from defining an incomplete “global” family. Phase 11 never refits a model or overwrites an upstream result.

The family names, BH method, alpha, and Yu fold-change threshold are frozen in `config/analysis_parameters.yml`. The shared `scripts/11_apply_multiple_testing.R` script emits separate gene, pathway, and similarity tables with explicit within-result and global family identifiers.

### Local pilot: apply pilot-wide correction families

- **Input:** validated local Phase 07-10 gene, pathway, similarity, annotation, and status artifacts.
- **Output:** corrected tables and validation artifacts under `results/local_pilot/11_multiple_testing/`; all are labeled `local_pilot` and `nonfinal_smoke_test`.
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase multiple_testing
```

### Minerva production: apply study-wide correction families

- **Input:** all validated Minerva Phase 07-10 result/status bundles. Do not launch until every intended per-RDS Phase 07-09 task and global Phase 10 task has a terminal validated status.
- **Output:** final corrected tables and validation artifacts under `results/minerva_production/11_multiple_testing/`.
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase multiple_testing
```

- **Expected outcome:** `multiple_testing_status.tsv` is `validated_complete`; every p-value has an explicit family/scope; upstream checksums are unchanged; and the output distinguishes within-group effects, tested interactions, unequal-power caveats, and absence of evidence.

If LSF fallback replaces an upstream result, rerun Phase 11 after the replacement bundle validates so the global family contains exactly the final accepted inputs.

## 19. Phase 12: Sensitivity and Robustness Analyses

Repeat major conclusions under: pseudobulk versus MAST; primary QC versus exclusion of flagged nuclei; 20 versus 50 nuclei; `NormalizeData` versus separately stored SCTransform; alternative age and PMI encodings; with/without validated batch; leave-one-donor-out; donor bootstrap; per-object versus results-only harmonization; alternative external mitochondrial sets; and global versus within-contrast FDR.

### Approved required-versus-optional sensitivity policy

For the current production release, the following seven sensitivity branches are required: pseudobulk versus MAST, exclusion of flagged nuclei, the 50-nucleus minimum, alternative age/PMI encoding, leave-one-donor-out, donor bootstrap, and global versus within-contrast FDR. A required branch must be `validated_complete`; a failed or missing required branch blocks a final production label.

The following four branches are optional because their required inputs or frozen mappings are not available in the present project bundle:

1. `validated_batch_covariate`: no validated sequencing-batch field is available. A candidate field must not be modeled until its meaning and donor/sample mapping are validated.
2. `normalization_sctransform`: no separately stored, frozen SCTransform sensitivity artifact and assay mapping are available.
3. `per_object_vs_results_only_harmonization`: no prespecified per-object harmonized result bundle is available.
4. `alternative_external_mitochondrial_sets`: no validated alternative external mitochondrial gene set is frozen in the scientific configuration.

An unavailable optional branch is terminal as `not_estimable`, not a failed analysis, provided its status names the missing input, records a nonempty reason, and is carried into the limitations report. It does not prevent `output_status = final` when all seven required branches validate and all other Phase 12 checks pass. If an optional input is later obtained and declared, that branch must be implemented and validated before its result is interpreted; an attempted branch that fails remains a blocker. Do not obtain a final label by editing an existing status file. Implement this policy in the shared Phase 12 and Phase 14 code, rerun the owning validation, and preserve the original primary outputs.

The initial Minerva production run produced 1,779,842 result rows, seven completed sensitivities, zero not-estimable sensitivities, four `blocked_missing_input` sensitivities, and 639,056 recorded conclusion changes. Its `partial_with_blocked_sensitivities` label reflects the older all-branches-required policy. Under the approved policy above, the four unavailable branches must be regenerated as documented optional `not_estimable` terminal records; the numerical results from the seven completed branches do not become invalid merely because those optional inputs are absent.

### Local pilot: exercise robustness code

- **Input:** local pilot cohort/QC, pseudobulk, MAST, pathway, and similarity outputs (~0.2-1 GB total).
- **Output:** `results/local_pilot/12_sensitivity/sensitivity_smoke.tsv` (<20 MB), robustness table (<10 MB), diagnostics (<10 MB), and validation/status artifacts.
- **What changes:** runs reduced checks sufficient to validate data flow and schemas; it does not overwrite primary results.
- **Create:** `scripts/12_sensitivity_analysis.R` (~20-40 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase sensitivity
```

- **Required output check:** every headline pilot result has direction/effect/FDR fields across applicable branches; all smoke outputs are labeled nonfinal.

### Minerva production: run all robustness checks

- **Input:** validated completed Minerva result bundles (~0.2-7 GB) and QC summaries (~0.1-2 GB).
- **Output:** sensitivity outputs under `results/minerva_production/12_sensitivity/` (~0.1-2 GB if complete).
- **What changes:** runs dependency-complete sensitivity tasks under the 12-hour guard; primary outputs remain unchanged.
- **Create:** the `sensitivity` mode in `scripts/run_pipeline.R` (~20-40 KB).
- **MKL requirement:** initialize the shell using Section 7.3, including the Intel Parallel Studio XE 2019 MKL paths and the representative MKL preflight. Use the scoped `LD_PRELOAD="$MKL_PRELOAD"` prefix for both the dry run and execution; defining `MKL_PRELOAD` alone does not affect the dynamic loader, and `LD_PRELOAD` should not be exported globally for unrelated commands.
- **Execute:**

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase sensitivity
```

- **Required output check:** all seven required branches are `validated_complete`; each of the four optional branches is either `validated_complete` or documented `not_estimable`; no attempted branch failed; and all statuses carry provenance. A production grid satisfying this approved policy may be labeled `final` even when an optional branch is not estimable.

### LSF fallback: run affected robustness tasks

- **Input:** validated Minerva production bundles plus any replacement bundles produced for unresolved tasks by the optional LSF fallback (~0.2-7 GB), and QC summaries (~0.1-2 GB).
- **Output:** sensitivity results under `results/minerva_production/12_sensitivity/` (~0.1-2 GB).
- **What changes:** reruns declared alternative models and compares compact results; primary bundles remain unchanged.
- **Create:** the sensitivity call in `jobs/09_downstream.lsf` (~3-8 KB), invoking `scripts/12_sensitivity_analysis.R` (~20-40 KB).
- **Execute:**

```bash
bsub < jobs/09_downstream.lsf
```

- **Required output check:** each prespecified sensitivity has a terminal status; required branches are complete; unavailable optional branches are documented as not estimable; and robustness tables show direction, effect, interval, FDR, and conclusion changes where applicable.

## 20. Phase 13: Power Analysis

The small and unequal strata are a central limitation; male epsilon2 begins with only 13 donors before cell-type filtering. Use the companion `scPower.ROSMAP.Rmd` and Yu et al.'s scDesign3 strategy as references, adapted to observed mitochondrial detection and donor-level variability. Estimate minimum detectable effects for representative abundant and rare cell types, and use power to qualify null results rather than post hoc filter them.

### Local pilot: smoke-test simulations

- **Input:** validated Phase 06 mitochondrial-detection summaries, Phase 07 pseudobulk count bundles/sample metadata, and the frozen eligible contrast manifest.
- **Output:** `results/local_pilot/13_power/power_smoke.tsv`, `power_grid.tsv`, `power_mde.tsv`, simulation diagnostics, checks, artifacts, and status.
- **What changes:** runs a small seeded simulation grid to verify code, schemas, and resource estimates; it does not overwrite upstream results.
- **Create:** the shared `scripts/13_power_analysis.R`, executed unchanged in local pilot and Minerva production.
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase power
```

- **Required output check:** seeds and assumptions are recorded; donor-level edgeR with observed dispersion and the paper-like cell-level hurdle branch both run; rare and abundant cell types, low- and high-detection mtDNA genes, zero and positive effects, and limiting/better-powered eligible contrasts are represented; every pilot condition reaches 10 repetitions; outputs are `validated_complete` and labeled `nonfinal_smoke_test`.

### Minerva production: run final power simulations

- **Input:** observed Minerva parameter summaries (~1-200 MB) and the prespecified simulation grid (~5-10 KB).
- **Output:** final power outputs under `results/minerva_production/13_power/`.
- **What changes:** runs every prespecified grid row to its final repetition target, stopping safely before each allocation's wall-time cutoff and resuming in later Minerva production allocations as needed.
- **MKL requirement:** run the Section 7.3 Minerva environment preflight and use the scoped `LD_PRELOAD="$MKL_PRELOAD"` prefix because the pseudobulk simulation branch invokes edgeR.
- **Execute:**

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase power
```

- **Required output check:** every grid condition reaches the final repetition target in Minerva production; repetitions, seeds, elapsed time, and status are explicit. Missing rows are resumed in Minerva production or moved to optional LSF fallback only when the activation criteria are met.

### LSF fallback: complete unresolved simulation rows

- **Input:** observed Minerva production parameter summaries (~1-200 MB), the prespecified simulation grid (~5-10 KB), and the unresolved grid rows selected for optional LSF fallback.
- **Output:** final power results under `results/minerva_production/13_power/`.
- **What changes:** runs at least 100 repetitions per condition and summarizes power, false discovery rate, and minimum detectable effects.
- **Create:** the power call in `jobs/09_downstream.lsf` (~3-8 KB), invoking `scripts/13_power_analysis.R` (~20-40 KB).
- **Execute:**

```bash
bsub < jobs/09_downstream.lsf
```

- **Required output check:** every grid condition has at least 100 completed repetitions or an explicit failure; seeds, fitted parameters, and resource use are saved.

## 21. Phase 14: Validation Strategy

### High-level validation

Internally, verify the known `MT-ND2` signal and paper-reported mitochondrial enrichment; compare pseudobulk, MAST, QC sensitivities, donor bootstrap, and leave-one-out results; check that pathway effects are not driven by one transcript; and confirm that total UMI or `percent.mt` alone does not explain the result.

Externally, prioritize an independent human brain dataset with diagnosis, sex, APOE, donor identity, and comparable cortical cell types. Emphasize pathway direction and cell-class consistency when exact genes are platform-sensitive. RNA expression cannot by itself establish respiration, membrane potential, ATP production, mtDNA copy number, or heteroplasmy.

### Local pilot: rerun and freeze the pilot

- **Input:** all local pilot outputs (~0.2-2 GB), status files (<10 MB), configuration checksums (<100 KB), logs (<100 MB), and resource measurements (<10 MB).
- **Output:** clean rerun `results/local_pilot_rerun/` (~0.2-2 GB), `results/local_pilot/11_validation/local_pilot_validation_report.tsv` (<1 MB), `local_pilot_minerva_production_task_graph_diff.tsv` (<1 MB), `local_pilot_parity_reference.tsv` (<1 MB), `local_pilot_completion_manifest.tsv` (<1 MB), and `local_pilot_promotion_checklist.md` (~10-30 KB).
- **What changes:** reruns into a separate output root; validates schemas, checksums, count conservation, cohort checkpoints, statuses, and deterministic outputs; and compares the local pilot dry-run graph with the Minerva production Vasculature subset. First-run results and inputs remain unchanged.
- **Create:** shared `scripts/run_pipeline.R` (~20-40 KB), shared `scripts/run_one_rds.R` (~10-20 KB), `scripts/14_validate_execution_parity.R` (~8-15 KB), `scripts/14_validate_outputs.R` (~10-20 KB), and `config/phase1_rerun.yml` (~1-2 KB), which changes only the output root relative to the first local pilot run.
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/phase1_rerun.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase all

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase all \
  --dry-run \
  --task-graph-output results/local_pilot/11_validation/local_pilot_task_graph.tsv

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase all \
  --dry-run \
  --task-graph-output results/local_pilot/11_validation/minerva_production_task_graph.tsv

Rscript scripts/14_validate_execution_parity.R \
  --local-pilot-task-graph results/local_pilot/11_validation/local_pilot_task_graph.tsv \
  --minerva-production-task-graph results/local_pilot/11_validation/minerva_production_task_graph.tsv \
  --require-task-subset \
  --require-code-checksum-match

Rscript scripts/14_validate_outputs.R \
  --config config/local_pilot.yml \
  --reference results/local_pilot \
  --candidate results/local_pilot_rerun
```

- **Required output check:** all terminal statuses are present; results match within declared tolerances; local pilot stable task IDs form a subset of Minerva production; corresponding tasks have identical scientific script paths, code checksums, argument names, schemas, and non-pilot scientific parameters; every promotion-gate item in Section 7.5 passes.

### Minerva production: confirm on-demand parity

- **Input:** Minerva Vasculature RDS (~138 MiB), local pilot parity reference (<1 MB), promoted code (~0.2-0.5 MB), and Minerva production config (~2-5 KB).
- **Output:** `results/minerva_production/00_parity/phase2_vasculature_parity.tsv` (<1 MB), logs (<10 MB), and status (<100 KB).
- **What changes:** reruns representative Vasculature operations on the on-demand node and compares them with local pilot.
- **Create:** the `parity` mode in `scripts/run_pipeline.R` (~20-40 KB) and `scripts/14_validate_execution_parity.R` (~8-15 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase parity
```

- **Required output check:** same 274 donors, dimensions, count checksums, pseudobulk sums, schemas, and compatible coefficients. Stop Minerva production scale-up if parity fails.

### LSF fallback: confirm Minerva parity

- **Input:** server Vasculature RDS (~138 MiB), LSF fallback configuration (~2-5 KB), promoted scripts (~0.2-0.5 MB total), and local pilot parity reference (<1 MB).
- **Output:** `results/minerva_production/00_parity/vasculature_parity.tsv` (<1 MB), parity logs (<10 MB), and status (<100 KB).
- **What changes:** reruns representative Vasculature work on Minerva and compares it with local pilot. Source data are unchanged.
- **Create:** `scripts/14_validate_execution_parity.R` (~8-15 KB) and `jobs/01_vasculature_parity.lsf` (~2-5 KB).
- **Execute:**

```bash
bsub < jobs/01_vasculature_parity.lsf
```

- **Required output check:** same 274 donors, dimensions, raw-count checksums, pseudobulk sums, schemas, and numerically compatible coefficients. Stop all optional LSF fallback submissions if parity fails.

### Minerva production: validate production completion

- **Input:** all Minerva production outputs/statuses (up to ~0.2-17 GB excluding normalized RDS), manifests (~0.1-5 MB), logs (<1 GB), and local pilot parity reference (<1 MB).
- **Output:** completion, validation, artifact-audit, resource, and status tables under `results/minerva_production/14_validation/` (<5 MB each).
- **What changes:** validates checksums, schemas, terminal statuses, and resumability; no scientific output is modified.
- **Create:** the `validate` mode in `scripts/run_pipeline.R` (~20-40 KB), calling `scripts/14_validate_outputs.R` (~10-20 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase validate
```

- **Required output check:** every planned task is validated, pending, failed, not started, or stopped for wall time. `validation_status = validated_complete` confirms that the completion audit itself passed; it does not make the production run final when `promotion_status = blocked`. Mark Minerva production final and skip LSF fallback only when both validation is complete and promotion is ready.

#### Minerva Phase 14 validation versus promotion blockers

The completed Minerva validation run reported 89 expected tasks, 89 validated tasks, zero required scientific-check failures, zero invalid declared artifacts, and `validation_status = validated_complete`. The recurring `rl_readline_state` loader warning is non-blocking when the controller reaches this terminal result. The same run reported `promotion_status = blocked`; this is a separate handoff decision rather than a failure of the 89 scientific task bundles.

Interpret and resolve promotion blockers as follows:

1. **`scientific_config_checksums_match_current_config`:** one or more task statuses were produced using an older complete-file SHA-256 for `config/analysis_parameters.yml`. The Minerva diagnostic identified 76 affected status records: environment (1), audit (9), cohort (1), annotations (1), QC (9), normalization (9), pseudobulk construction (9), contrast construction (1), pseudobulk DE (9), MAST (9), mitochondrial-fraction analysis (9), and pathways (9). Repository-history and script-usage review showed that the checksum changes came from later reference-provenance fields, QC/reporting settings, and downstream multiple-testing-family definitions rather than changes to the scientific parameters consumed by those already-completed tasks. Therefore, do not rerun these 76 tasks solely to replace their whole-file checksum. Implement and audit phase-specific configuration fingerprints, or an explicit compatibility record listing the keys consumed by each task mode. A task requires rerunning only when a consumed scientific key, its scientific script, or a validated upstream artifact changed. Preserve the old and current whole-file hashes as provenance, and never edit a status hash manually.
2. **`clean_rerun_output_exists`:** this is a local-pilot-only promotion requirement and is not applicable to `minerva_production`. Do not create a fake `results/minerva_production_rerun/` directory. The validator must treat this check as automatically satisfied or not applicable when `execution_stage != local_pilot`; until that correction is synchronized, record this blocker as a validator defect rather than a missing production artifact.
3. **`execution_task_graph_parity_available`:** Phase 14 could not find an accepted local-pilot/Minerva parity artifact. Run the Phase 14 parity procedure above with the exact promoted revision and require matching Vasculature donors, dimensions, raw-count and pseudobulk checksums, script/config interfaces, schemas, and compatible coefficients. Save the validated parity artifact where the completion validator expects it, then rerun `--phase validate`. Do not waive a true parity mismatch.
4. **`output_labels_match_execution_scope`:** the Minerva diagnostic identified only `global:sensitivity`, labeled `partial_with_blocked_sensitivities`. The four unavailable branches listed in Section 19 are approved as optional/not estimable for the current release; they must retain explicit missing-input reasons and appear in the limitations report, but they do not block a final label when the seven required branches validate. Update the shared Phase 12/14 policy, regenerate the owning status and validation artifacts, and never change an output label by editing a status file. Any unrelated `nonfinal_smoke_test`, failed required branch, or attempted optional branch that failed remains a real blocker.

The `bit64` warnings emitted by the diagnostic affect only how `integer64` columns print. They do not change the stored values or scientific results and are not promotion blockers; installing `bit64` is optional for cleaner interactive display.

The approved resolution of the four blockers is therefore:

- use audited task-specific configuration compatibility for the 76 historical status records instead of forcing scientific reruns;
- mark the clean-rerun requirement not applicable to `minerva_production` while retaining it for `local_pilot`;
- implement and run the declared execution task-graph parity validator, treating a real parity mismatch as blocking;
- apply the Section 19 required-versus-optional sensitivity policy and regenerate Phase 12/14 status artifacts.

These are validator/provenance corrections. They do not waive failed scientific checks, authorize manual status edits, or by themselves set `promotion_status = ready`. Promotion is ready only after the corrected shared code is synchronized, the parity artifact validates, and a fresh Phase 14 run reports no blockers.

Use this diagnostic from the project root after any Phase 14 run that validates but remains promotion-blocked:

```bash
Rscript -e '
library(data.table)

path <- "results/minerva_production/14_validation/minerva_production_completion_manifest.tsv"
x <- fread(path)

cat("Tasks with older scientific configuration:\n")
config_bad <- x[
  is.na(scientific_config_sha256_matches) |
    !scientific_config_sha256_matches
]
print(config_bad[, .(
  affected_tasks = .N,
  recorded_config_versions = uniqueN(recorded_scientific_config_sha256)
), by = task_mode])

cat("\nNon-final output labels:\n")
labels <- rbindlist(lapply(seq_len(nrow(x)), function(i) {
  status_path <- x$expected_status_path[[i]]
  if (!file.exists(status_path)) return(NULL)

  status <- fread(status_path)
  if (!"output_status" %in% names(status)) return(NULL)

  data.table(
    stable_task_id = x$stable_task_id[[i]],
    output_status = unique(as.character(status$output_status))
  )
}), fill = TRUE)
print(labels[output_status != "final"])
'
```

After resolving or correctly marking each blocker as not applicable, rerun the same `--phase validate` command. The promotion gate passes only when `validation_status = validated_complete`, `promotion_status = ready`, and `promotion_blockers` is empty.

### LSF fallback: merge and validate production outputs

- **Input:** all validated Minerva production bundles plus any replacement bundles from optional LSF fallback (~0.2-17 GB depending on retained simulations), RDS/contrast manifests (~0.1-5 MB), local pilot parity reference (<1 MB), and logs/statuses (~10 MB-1 GB).
- **Output:** consolidated result tables (~0.2-7 GB), `minerva_completion_manifest.tsv` (~0.1-5 MB), `minerva_validation_report.tsv` (<5 MB), and `minerva_run_report.md` (~20-100 KB).
- **What changes:** validates schemas and unique keys, combines compact result files, and reconciles expected versus observed outputs. Upstream bundles remain unchanged.
- **Create:** `scripts/14_merge_results.R` (~10-20 KB), promoted `scripts/14_validate_outputs.R` (~10-20 KB), and `jobs/10_finalize.lsf` (~3-8 KB).
- **Execute:**

```bash
bsub < jobs/10_finalize.lsf
```

- **Required output check:** every RDS and contrast has one terminal status; no unexplained missing/duplicate outputs remain; the report records revision, checksums, package versions, resources, and limitations.

## 22. Phase 15: Figures and Tables

Generate representative Vasculature outputs in local pilot and complete 54-cell-type final outputs in Minerva production. If optional LSF fallback is activated, regenerate only figures affected by replacement or newly completed fallback results. Core products are the cohort flow, group coverage, mitochondrial count/fraction summaries, mtDNA and pathway effects, mitonuclear balance, similarity, robustness, and power figures. Every inferential figure must show donor counts.

### Local pilot: render pilot figures

- **Input:** validated local pilot cohort, QC, model, pathway, similarity, sensitivity, and power tables (~0.2-1 GB total).
- **Output:** representative figures under `results/local_pilot/15_figures/` (~20-200 MB) and a figure manifest (<1 MB).
- **What changes:** renders plots from compact tables only; no analysis result is changed.
- **Create:** `scripts/15_make_figures.R` (~20-40 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase figures
```

- **Required output check:** each figure uses a stage-neutral title, displays donor counts where applicable, and has a manifest row linking it to source tables. The PDF must not display the phase, execution stage, or output status; `figure_manifest.tsv` and `figure_status.tsv` retain `local_pilot` and `nonfinal_smoke_test` provenance.

### Minerva production: render final Minerva figures

- **Input:** complete validated Minerva production compact tables (~0.2-7 GB) and figure parameters (~5-10 KB).
- **Output:** final figures under `results/minerva_production/15_figures/` (~20-500 MB) and manifest (<5 MB).
- **What changes:** applies final ordering and labels and renders publication-ready plots from the complete Minerva production results.
- **Create:** the `figures` mode in `scripts/run_pipeline.R` (~20-40 KB), calling `scripts/15_make_figures.R` (~20-40 KB).
- **Execute:**

```bash
Rscript scripts/run_pipeline.R --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml --phase figures
```

- **Required output check:** all planned final figures exist or have explicit not-estimable reasons; donor counts are visible; provenance is recorded in the manifest/status tables; no figure displays the phase, execution stage, or output status; and no figure treats nuclei as independent sample size.

### LSF fallback: rerender affected final figures

- **Input:** validated Minerva production tables plus only the replacement or newly completed results from optional LSF fallback (~0.2-7 GB), and figure parameters (~5-10 KB).
- **Output:** final figures under `results/minerva_production/15_figures/` (~20-500 MB) and a figure manifest (<5 MB).
- **What changes:** rerenders only affected final panels after reconciling Minerva production and fallback results; source tables remain unchanged.
- **Create:** the figure call in `jobs/10_finalize.lsf` (~3-8 KB), invoking `scripts/15_make_figures.R` (~20-40 KB).
- **Execute:**

```bash
bsub < jobs/10_finalize.lsf
```

- **Required output check:** all planned final figures exist or have explicit not-estimable reasons; donor counts are visible; provenance is recorded in the manifest/status tables; no figure displays the phase, execution stage, or output status; and no figure treats nuclei as independent sample size.

## 23. Phase Dependency and Execution Index

The concrete runbook now lives inside the phase that owns each operation. Use this dependency order:


### Required local-to-Minerva handoff for every Minerva production scientific section

Do not run a Minerva production scientific command merely because its corresponding local section passed. First complete the entire local pilot, pass every Section 7.5 local-pilot-to-Minerva-production promotion gate, commit the promoted scripts/configuration/lockfile, synchronize that exact Git revision to Minerva, and rerun the Section 7.3 environment preflight until it reports `validated_complete`. Minerva production must use the promoted scientific scripts unchanged; only the Minerva config, manifest scope, resource values, and output root may differ.

Before the first nine-RDS task, run the Section 21 `parity` phase and stop if it does not validate. For every controller task-mode value in the table below, run this exact Minerva sequence from the project root in the same configured module/proxy environment:

```bash
# Replace this value with the next phase from the table below.
MODE=audit

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase "$MODE" \
  --dry-run

Rscript -e '
mode <- commandArgs(trailingOnly = TRUE)[[1L]]
path <- file.path(
  "results/minerva_production/00_environment",
  paste0("minerva_production_", mode, "_task_graph.tsv")
)
graph <- read.delim(path, check.names = FALSE)
print(graph[, c("stable_task_id", "task_mode", "rds_id", "scientific_script", "script_exists")])
stopifnot(
  nrow(graph) > 0L,
  !anyDuplicated(graph$stable_task_id),
  all(graph$script_exists),
  all(!is.na(graph$scientific_script_sha256) & nzchar(graph$scientific_script_sha256))
)
' "$MODE"

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase "$MODE"
```

Expected dry-run outcome for every controller task mode: exit code zero; only the intended stable task IDs; no duplicate task IDs; every scientific script exists; and every script has a nonmissing promoted checksum. Expected execution outcome: the section-specific output/status bundle exists, all completed items pass the listed scientific assertions, and every intended task is represented by `validated_complete`, `failed`, `not_started`, or `stopped_for_walltime`. Do not advance a dependent phase when an upstream item is failed or incomplete; resume Minerva production unless the Section 7.4 LSF fallback activation criteria are met.

| Order after local promotion | Set `MODE=` to | Run on Minerva after | Expected successful outcome before advancing |
| --- | --- | --- | --- |
| Phase 14 pre-scale parity (Section 21) | `parity` | local pilot promotion artifacts and Vasculature reference outputs are synchronized | Vasculature has the same 274 donors, dimensions, raw-count checksums, pseudobulk sums, schemas, and compatible coefficients as local pilot. Stop all scale-up if parity fails. |
| Phase 01 (Section 8) | `audit` | Parity passes; all nine RDS inputs and master metadata are present | Nine unique audit statuses are `validated_complete`; dimensions, sparse integer counts, donor/cell-type coverage, 13 mtDNA genes, metadata agreement, and peak RAM are recorded. Section 8 also contains the exact audit-specific dry-run and status-check commands. |
| Phase 02 (Section 9) | `cohort` | All required audits validate | Global cohort contains 276 donors; each audited RDS has an explicit eligible-donor intersection; cohort-definition checksum matches local pilot. |
| Phase 03 (Section 10) | `annotations` | Cohort succeeds and frozen GENCODE/MitoCarta files are present | GENCODE SHA-256 is `3e52f82c63f8fd860bf632ccde10441c05751f4c342ad08c0a98e9e2700171a5`; reference checksums match local pilot; every RDS has explicit measured and tested gene universes. |
| Phase 04 (Section 11) | `qc` | Audit, cohort, and annotations succeed | Every launched RDS has a terminal status and measured peak RAM; mitochondrial counts are nonnegative and `percent.mt` is finite and within 0-100. |
| Phase 05 (Section 12) | `normalize` | That RDS's QC validates | Each completed normalized RDS reloads; dimensions and raw-count checksums equal its source; metadata assertions and sampled normalization-formula checks pass. |
| Phase 06 (Section 13) | `descriptive` | Cohort/QC inputs needed for summaries validate | All 54 expected fine cell types are represented or explicitly reported missing; donor/nucleus totals reconcile; all 12 sex-APOE-diagnosis groups, including zero-count groups, are shown. |
| Phase 07.1 (Section 14) | `pseudobulk` | Cohort, QC, and required normalized/metadata artifacts validate | Every completed RDS passes exact gene-wise and total UMI conservation; one sample-metadata row exists per pseudobulk column. |
| Phase 07.2 (Section 14) | `contrasts` | All usable pseudobulk summaries validate | Exactly 324 planned paper-matched rows exist before eligibility filtering; each is eligible, ineligible, or blocked-pending with donor counts and source provenance. |
| Phase 07.3 (Section 14) | `pseudobulk_de` | Contrast manifest is frozen | Every eligible edgeR contrast has one terminal status, donor counts, effect sizes, result provenance, and unique `(cell_type, contrast, gene)` keys. |
| Phase 08 (Section 15) | `mast` | Eligible contrast manifest and normalized inputs validate | Every eligible MAST task records cell counts and donor counts separately, source RDS, peak RAM, schema, and terminal status. |
| Phase 09.1 (Section 16) | `mito_fraction` | Primary model dependencies validate | Every modeled mitochondrial fraction/ratio records numerator, denominator, covariates, tested population, and terminal status. |
| Phase 09.2 (Section 16) | `pathways` | Annotation universes and eligible primary models validate | Every estimable pathway/mitonuclear test records its gene universe and multiple-testing family; incomplete dependencies are explicitly blocked. |
| Phase 10 (Section 17) | `similarity` | Required primary and secondary result branches validate | Final outputs are labeled production, use 10,000 recorded permutations, retain separate pseudobulk/MAST branches, and record seeds and terminal statuses. |
| Phase 11 (Section 18) | `multiple_testing` | All accepted Phase 07-10 result/status bundles validate | Global mtDNA, MitoCarta, pathway, genome-wide sensitivity, and similarity families validate; upstream checksums are unchanged; every p-value has an explicit family/scope. |
| Phase 12 (Section 19) | `sensitivity` | Headline Phases 07-09 results validate | Every prespecified sensitivity is complete, blocked, or pending with direction, effect, interval, FDR, provenance, and conclusion-change fields. |
| Phase 13 (Section 20) | `power` | Frozen model/design inputs are available | Every final grid condition records at least the planned 100 repetitions, seeds, assumptions, elapsed time, and terminal status. |
| Phase 14 (Section 21) | `validate` | All intended scientific phases have terminal statuses | Completion manifest classifies every planned task; no unexplained missing or duplicate outputs remain; if all validate, Minerva production is final and LSF fallback is skipped. |
| Phase 15 (Section 22) | `figures` | Final validation inputs needed by each figure are valid | Every planned final figure exists or has an explicit not-estimable reason; stage-neutral PDFs display donor counts where applicable; provenance remains in the manifest/status tables; nuclei are not treated as independent sample size. |

For multi-step phases, run the rows sequentially and repeat the dry-run/check/execute sequence for each value: Phase 07 is `pseudobulk` then `contrasts` then `pseudobulk_de`; Phase 09 is `mito_fraction` then `pathways`. Never use `--phase all` as a shortcut until all individual phase scripts exist, all upstream dependencies validate, and the complete dry-run graph passes the promotion checks.

1. Phase 00 creates and checks the shared configuration and computing environment.
2. Phase 01 audits inputs.
3. Phase 02 freezes the donor cohort.
4. Phase 03 freezes mitochondrial annotations.
5. Phase 04 calculates raw-count QC.
6. Phase 05 attaches metadata and normalizes working objects.
7. Phase 06 reports descriptive coverage.
8. Phase 07 builds pseudobulk data, freezes contrasts, and runs primary edgeR models.
9. Phase 08 runs the secondary paper-comparable MAST branch.
10. Phase 09 models mitochondrial read fraction and runs pathway/mitonuclear analyses.
11. Phase 10 runs Zhang-Yu similarity.
12. Phases 11-13 apply multiple-testing rules, robustness analyses, and power analysis.
13. Phase 14 validates outputs, and Phase 15 renders figures and tables.

Within each execution environment, follow the dependency table above. Numeric phase IDs are stable scientific identifiers; Phase 14 parity is deliberately invoked both before Minerva scale-up and during final validation. The local pilot must pass the Section 7.5 local promotion gate. Minerva production begins with Minerva parity and runs the complete approximately 2.3-million-nucleus production manifest through final validation and figures. If Minerva production validates completely, stop there. Optional LSF fallback imports the completion manifest and uses LSF only for tasks whose documented Minerva production failure meets the activation criteria. New orchestration records use the named `execution_stage`; `execution_phase` may remain in older status rows only as a deprecated compatibility code.

## 24. Shared Files to Create

The phase sections reference the following planned implementation files. Create the shared scientific scripts, shared task runner, and shared controller during local pilot, then freeze and reuse them unchanged in Minerva production. Only configs and manifests are environment-specific. Create LSF configuration and wrappers only if optional LSF fallback is activated.

| Planned file | Estimated size | First executed in |
| --- | ---: | --- |
| `config/analysis_parameters.yml` | ~5-10 KB | Section 7, local pilot |
| `config/local_pilot.yml` | ~2-5 KB | Section 7, local pilot |
| `config/local_pilot_execution.yml` | ~2-5 KB | Section 7, local pilot |
| `config/phase1_rerun.yml` | ~1-2 KB | Section 21, local pilot clean rerun |
| `config/local_pilot_rds_manifest.tsv` | ~1 KB | Section 7, local pilot |
| `config/minerva_shared.yml` | ~2-5 KB | local pilot task-graph dry run; Minerva production and LSF fallback |
| `config/minerva_rds_manifest.tsv` | ~2-5 KB | local pilot task-graph dry run; Minerva production and LSF fallback |
| `config/minerva_production_execution.yml` | ~2-5 KB | local pilot task-graph dry run; Minerva production |
| `config/phase3_lsf.yml` | ~2-5 KB | Section 7, optional LSF fallback |
| `scripts/00_check_environment.R` | ~5-10 KB | Section 7 |
| `scripts/run_one_rds.R` | ~10-20 KB | Shared task orchestration, local pilot, Minerva production, and LSF fallback |
| `scripts/run_pipeline.R` | ~20-40 KB | Section 7, local pilot; unchanged in Minerva production |
| `scripts/01_audit_seurat_inputs.R` | ~10-20 KB | Phase 01 |
| `scripts/02_build_cohort.R` | ~10-20 KB | Phase 02 |
| `scripts/03_build_mito_annotations.R` | ~10-20 KB | Phase 03 |
| `scripts/04_mito_qc.R` | ~10-20 KB | Phase 04 |
| `scripts/05_normalize_and_attach_metadata.R` | ~10-20 KB | Phase 05 |
| `scripts/06_summarize_celltypes.R` | ~10-20 KB | Phase 06 |
| `scripts/07_make_pseudobulk.R` | ~10-20 KB | Phase 07 |
| `scripts/07_build_contrast_manifest.R` | ~8-15 KB | Phase 07 |
| `scripts/07_run_pseudobulk_de.R` | ~15-30 KB | Phase 07 |
| `scripts/08_run_mast.R` | ~15-30 KB | Phase 08 |
| `scripts/09_run_mito_fraction_models.R` | ~10-20 KB | Phase 09 |
| `scripts/09_run_mito_pathways.R` | ~15-30 KB | Phase 09 |
| `scripts/10_similarity_analysis.R` | ~15-30 KB | Phase 10 |
| `scripts/11_apply_multiple_testing.R` | ~15-30 KB | Phase 11 |
| `scripts/12_sensitivity_analysis.R` | ~20-40 KB | Phase 12 |
| `scripts/13_power_analysis.R` | ~20-40 KB | Phase 13 |
| `scripts/14_validate_outputs.R` | ~10-20 KB | Phase 14 |
| `scripts/15_make_figures.R` | ~20-40 KB | Phase 15 |
| `scripts/reconcile_phase_handoff.R` | ~10-20 KB | Section 7, optional LSF fallback |
| `scripts/14_merge_results.R` | ~10-20 KB | Phase 14, optional LSF fallback |
| `scripts/14_validate_execution_parity.R` | ~8-15 KB | Phase 14, local pilot code-path subset check; Minerva production and optional LSF fallback parity |
| `jobs/00_check_environment.lsf` | ~2-5 KB | Section 7, Optional LSF fallback only |
| `jobs/01_vasculature_parity.lsf` | ~2-5 KB | Phase 14, Optional LSF fallback only |
| `jobs/02_audit_rds_array.lsf` | ~2-5 KB | Phase 01, Optional LSF fallback only |
| `jobs/03_cohort_annotations.lsf` | ~2-5 KB | Phases 02-03, Optional LSF fallback only |
| `jobs/04_qc_normalize_rds_array.lsf` | ~3-8 KB | Phases 04-05, Optional LSF fallback only |
| `jobs/05_descriptive.lsf` | ~2-5 KB | Phase 06, Optional LSF fallback only |
| `jobs/05_pseudobulk_rds_array.lsf` | ~2-5 KB | Phase 07, Optional LSF fallback only |
| `jobs/06_build_contrast_manifest.lsf` | ~2-5 KB | Phase 07, Optional LSF fallback only |
| `jobs/07_pseudobulk_de_array.lsf` | ~3-8 KB | Phase 07, Optional LSF fallback only |
| `jobs/08_mast_array.lsf` | ~3-8 KB | Phase 08, Optional LSF fallback only |
| `jobs/09_downstream.lsf` | ~3-8 KB | Phases 09-13, Optional LSF fallback only |
| `jobs/10_finalize.lsf` | ~3-8 KB | Phases 14-15, Optional LSF fallback only |
| `jobs/submit_phase3_lsf.sh` | ~5-15 KB | Phases 07-08, Optional LSF fallback only |

Every scientific script listed above is used by both local pilot and Minerva production and reads scientific definitions from `config/analysis_parameters.yml`; execution files supply paths, selected task IDs, pilot limits, and resources. No scientific script may contain environment-specific algorithm branches. Every output table contains execution environment, backend, run ID, stable task ID, source RDS, revision, scientific code-bundle checksum, resolved scientific-configuration checksum, manifest checksum, and status/provenance fields.

## 25. Quality-Control Checklist Before Reporting a Finding

A finding can be called a robust mitochondrial result only if:

- The cohort and donor counts pass all checkpoints.
- The gene or pathway was defined before final hypothesis testing.
- Raw counts, not normalized or integrated values, were used for pseudobulk count models.
- The result has sufficient donors and is not driven by one donor.
- The interaction is directly tested when claiming a sex or APOE difference.
- Effect direction and magnitude are reasonably stable across pseudobulk and sensitivity analyses.
- Multiple-testing correction uses the declared family.
- The result is not explained solely by total RNA count or mitochondrial read fraction.
- Detection rate and measurable dynamic range are adequate.
- The language distinguishes expression from mitochondrial function.

## 26. Main Risks and Mitigations

| Risk | Consequence | Mitigation |
| --- | --- | --- |
| Small epsilon2 strata | Unstable estimates and false negatives | Donor-count gates, confidence intervals, power simulation, bootstrap, and cautious language. |
| Pseudoreplication | Inflated significance | Make donor-level pseudobulk primary; use MAST for paper comparability only. |
| Mitochondrial QC is also the target | Filtering or regression can erase biology | Keep original-QC nuclei in the primary analysis and use flagged-cell exclusion only as sensitivity. |
| Only 13 mtDNA protein genes are present | Limited direct mitochondrial-genome coverage | Add nuclear-encoded MitoCarta genes and pathway-level analyses; report absent rRNA/tRNA features. |
| Existing RDS normalization state varies | Incomparable expression layers | Recompute one uniform `NormalizeData` layer from preserved raw counts and validate it. |
| Missing batch metadata | Residual technical confounding | Search assay metadata, quantify available batch effects, and state clearly when batch cannot be modeled. |
| Age is censored as `90+` | Covariate ambiguity | Use a documented capped value and sensitivity indicator. |
| RNA does not measure mitochondrial function directly | Overinterpretation | Use expression-specific wording and propose functional follow-up. |
| Scientific parameters drift across local pilot, Minerva production, and LSF fallback | Earlier validation no longer supports production | Put scientific parameters in one shared file, checksum it, and reject any mismatched direct process or LSF job. |
| Environment-specific scientific code or wrapper logic | The pilot no longer validates production behavior | Use one shared controller and shared scientific scripts; restrict differences to validated configs/manifests; compare dry-run task graphs and code-bundle checksums before promotion. |
| Minerva and local package behavior differs | Platform-dependent results or failed jobs | Lock versions, run the Vasculature parity test, and compare numerical checkpoints before the full launch. |
| Large Minerva RDS files exceed initial requests | Killed or partially written jobs | Use one RDS per job, tier memory requests, write atomically, and retain explicit failed/retry statuses. |
| Hundreds of jobs yield missing or duplicate results | Incomplete or biased final result set | Drive execution from manifests and require one terminal status per input and contrast. |

## 27. Immediate Next Actions

### Local pilot actions

1. Create the shared scientific scripts, `scripts/run_one_rds.R`, and `scripts/run_pipeline.R`; create/check the shared scientific config, local-pilot configs/manifest, Minerva production dry-run configs/manifest, and local R environment.
2. Dry-run the Vasculature task graph with the local pilot and Minerva production configs and confirm that local-pilot task IDs and shared code paths are a strict subset of Minerva production.
3. Complete Phase 01 audit on the Vasculature RDS (~139 MB).
4. Complete Phase 02 cohort construction and Phase 03 annotation freezing.
5. Complete Phase 04 raw-count QC before Phase 05 normalization.
6. Complete Phase 06 descriptive coverage checks.
7. Run all Phase 07 pilot pseudobulk contrasts and the matching Phase 08 MAST contrasts.
8. Exercise Phases 09-15, then complete the clean rerun, code-path subset report, resource report, and promotion checklist.

### Minerva production actions after local promotion

1. Confirm the precreated `config/minerva_shared.yml` (~2-5 KB), `config/minerva_rds_manifest.tsv` (~2-5 KB), and `config/minerva_production_execution.yml` (~2-5 KB), changing only operational paths/resources if needed; do not edit promoted scientific or orchestration code.
2. Restore the promoted environment, verify shared code-bundle checksums, and run Vasculature parity.
3. Dry-run the 192 GiB/12-hour schedule and reconfirm that the local-pilot task graph is a subset of the resolved Minerva production graph.
4. Run the complete nine-RDS, approximately 2.3-million-nucleus manifest, resuming across on-demand allocations as needed.
5. Normalize large RDS files one at a time and run at most one MAST worker per source RDS.
6. Complete all downstream analyses and final figures, validate every output, and write the Minerva production completion manifest (<5 MB). Skip LSF fallback if all tasks validate.

### Optional LSF fallback actions only after a documented Minerva production failure

1. Confirm that at least one unresolved Minerva production task meets the Section 7.4 activation criteria; otherwise resume Minerva production or stop if Minerva production is complete.
2. Reconcile the Minerva production completion manifest (<5 MB) with `scripts/reconcile_phase_handoff.R` (~10-20 KB).
3. Create only the required `config/phase3_lsf.yml` (~2-5 KB) settings and LSF wrappers (~2-15 KB each), using measured Minerva production resources.
4. Dry-run reconciliation and submit only unresolved fallback task IDs; never resubmit validated Minerva production work.
5. Merge validated Minerva production outputs with fallback outputs and rerender only affected downstream products or figures.
6. Reconcile every expected output before biological interpretation, recording that LSF fallback changed only the backend and not the scientific scope.

## 28. Methodological Decisions to Confirm With the Professor

The plan can proceed with the defaults above, but these decisions should be documented after discussion:

1. Whether the intended primary scope is the 13 mtDNA genes, all MitoCarta genes, mitochondrial pathways, or all three. This plan recommends all three with separate testing families.
2. Whether paper-faithful MAST or donor-aware pseudobulk should be labeled primary. This plan recommends pseudobulk primary and MAST secondary.
3. Whether the full production manifest should include all 54 fine cell types immediately or use a prespecified priority order while still completing every planned row.
4. Whether a suitable independent brain dataset is already available for validation.
5. Whether sequencing batch, medication, neuropathology, ancestry, and additional technical covariates can be obtained.

## 29. Key References and Local Guides

- Yu et al. local paper: `docs/Yu_sex_apoe.pdf` (~2.3 MB).
- Local method summary: `docs/Yu_sex_apoe_method.md` (~11 KB).
- Professor's data and normalization instructions: `docs/email_07092026.txt` (~1.0 KB).
- Local Seurat-object tutorial: `docs/vasculature_cells_rds_structure.md` (~32 KB).
- Local data triage: `docs/yu_data_file_triage.md` (~8.9 KB).
- Local data-access notes: `docs/data_availability.md` (~12 KB).
- [Seurat `NormalizeData` reference](https://satijalab.org/seurat/reference/normalizedata).
- [Human MitoCarta3.0 inventory](https://www.broadinstitute.org/files/shared/metabolism/mitocarta/human.mitocarta3.0.html).
- [Confronting false discoveries in single-cell differential expression](https://www.nature.com/articles/s41467-021-25960-2), supporting donor-aware biological-replicate analysis.

## Bottom Line

The project uses one implementation across three execution environments. The local pilot runs a configured Vasculature subset locally (~139 MB; 5 fine cell types) through the same controller, scientific scripts, functions, CLI schemas, and validations used by Minerva production; only configs, manifests, resources, paths, task scope, and declared nonfinal pilot limits differ. Minerva production is the full production analysis of all nine RDS files (~34.9 GiB), approximately 2.3 million nuclei, and 54 fine cell types, including downstream analyses, validation, and final figures. LSF fallback is optional: run it only when documented Minerva production tasks are too slow, exceed memory or wall time, or otherwise fail on the on-demand node. It adds no data or scientific analysis and uses LSF only to finish the unresolved subset. If Minerva production validates completely, do not run LSF fallback.
