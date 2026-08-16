# WP5 implementation guide: human genetic support for Phase 18 key drivers

**Date:** 2026-08-16  
**Parent plan:** [Publication validation plan for the Phase 18 DEG/KDA findings](phase18_key_driver_cross_validation_guide.md)  
**Purpose:** Turn WP5 into a reproducible candidate-first analysis that distinguishes a nearby GWAS signal from genetic evidence that actually implicates a Phase 18 key driver.

## 1. What WP5 must answer

For each frozen Phase 18 candidate and broad-network context, answer:

> Is inherited variation associated with Alzheimer disease (AD) or a prespecified AD-related phenotype, and is there credible evidence connecting that variation to this candidate gene?

WP5 is not a search for any paper that mentions the gene. It is a structured assessment of four evidence routes:

1. a fine-mapped AD variant with a direct coding consequence in the candidate;
2. an AD signal that colocalizes with a candidate eQTL or sQTL, preferably in the matching brain cell type;
3. a fine-mapped non-coding AD signal connected to the candidate by a coherent regulatory chain; or
4. a corrected and preferably replicated rare-variant gene burden.

A lead variant near a gene, a nominal association, or a TWAS result without colocalization is weak evidence. Absence of genetic support does not invalidate a trans-acting network driver.

## 2. Pilot scope and analysis units

Start with the six candidates specified in the parent plan:

| Candidate | Frozen Phase 18 context to prioritize in WP5 |
|---|---|
| APOE | Astrocytes |
| SELENOW | Excitatory neurons |
| LAMTOR5 | Excitatory neurons; inhibitory neurons |
| RPL11 | Excitatory neurons; astrocytes |
| FTL | OPCs |
| ANKRD11 | OPCs |

The genetic locus is gene-specific, but QTL evidence is context-specific. Therefore:

- search common-variant, coding, and rare-variant evidence once per gene and reuse it across that gene's contexts;
- evaluate eQTL/sQTL/caQTL evidence separately for each `key_driver × broad_network`; and
- do not count one GWAS locus repeated across several Phase 18 contexts as independent genetic replication.

After the pilot works, extend exactly the same procedure to the remaining displayed genes. Mitochondrial DNA genes require the separate rules in Section 15.

## 3. Minimum viable route

This is the shortest defensible way to complete WP5 for the six pilot candidates.

1. Finish WP1 and freeze `phase18_validation_candidate_manifest.tsv`.
2. Make a candidate-locus table using stable Ensembl gene IDs and GRCh38 coordinates.
3. Register one primary clinically anchored AD GWAS and prespecified secondary phenotypes before looking at candidate results.
4. Search NIAGADS Alzheimer's GenomicsDB and the GWAS Catalog for discovery, but treat these searches only as a locus screen.
5. Download the FunGen-AD GRCh38 fine-mapping summary and precomputed AD-eQTL/sQTL colocalization results.
6. For every candidate, determine whether a fine-mapped AD variant has a coding consequence in the candidate or another defensible mapping to it.
7. Filter the precomputed colocalization results to the candidate's Ensembl ID and matched cell type. Check the GWAS, QTL phenotype, method, ancestry, and posterior fields.
8. If precomputed results are absent or ambiguous and full regional summary statistics plus suitable LD are available, run the custom colocalization workflow in Sections 10-11.
9. Search published/ADSP gene-based sequencing results using the rare-variant checklist in Section 12.
10. Grade evidence using Section 13 and write both detailed audit tables and the one-row-per-context summary required by the parent plan.

Do not substitute a gene-level GWAS Catalog hit list for steps 5-9.

## 4. Required inputs and output layout

### 4.1 Required frozen project input

Use:

```text
phase18_validation_candidate_manifest.tsv
```

At minimum, retain:

```text
key_driver
broad_network
case_id
within_case_rank
kda_run_id
fine_cell_type
sex
apoe_group
signature_direction
```

If the WP1 manifest does not yet exist, create it before interpreting external evidence. Do not silently reconstruct a different candidate set inside WP5.

### 4.2 Recommended output location

```text
results/minerva_production/18_key_driver_validation/wp5_human_genetics/
├── config/
├── metadata/
├── harmonized/
├── tables/
├── figures/
└── logs/
```

Keep downloaded public data in a separate data location if files are large. Keep controlled-access ADSP data only in the institutionally approved environment; do not copy it into the repository.

### 4.3 Required tables

Create these audit tables:

```text
phase18_wp5_candidate_loci.tsv
phase18_wp5_dataset_registry.tsv
phase18_wp5_common_variant_evidence.tsv
phase18_wp5_colocalization.tsv
phase18_wp5_rare_variant_evidence.tsv
phase18_wp5_assessability_qc.tsv
```

The final parent-plan deliverable is:

```text
phase18_human_genetic_evidence.tsv
```

It must have one row per frozen `key_driver × broad_network` context. The detailed tables preserve all individual studies, signals, and tests; the final table summarizes them.

## 5. Freeze the analysis before querying candidates

Write `config/wp5_analysis_specification.md` containing the following decisions.

### 5.1 Phenotype hierarchy

Use this default hierarchy unless the scientific question requires a documented change:

1. **Primary:** late-onset AD case-control GWAS with a clearly documented clinical or study-specific case definition.
2. **Secondary:** age at onset, amyloid, tau, neuropathology, cognitive decline, or other explicitly AD-related endophenotypes.
3. **Sensitivity:** proxy-AD or broad dementia GWAS.

Do not pool these phenotypes into one result. Proxy AD, broad dementia, and biomarker associations must remain labeled as such.

### 5.2 Context hierarchy for molecular QTLs

| Phase 18 network | Primary QTL context | Acceptable fallback, labeled secondary |
|---|---|---|
| Astrocytes | Astrocyte | Major-cell-type astrocyte, then bulk brain |
| Excitatory neurons | Excitatory neuron | Neuron, then bulk brain |
| Inhibitory neurons | Inhibitory neuron | Neuron, then bulk brain |
| OPCs | OPC | Oligodendrocyte-lineage or bulk brain |
| Oligodendrocytes | Oligodendrocyte | Oligodendrocyte-lineage or bulk brain |
| Microglia | Microglia | Myeloid/microglia bulk, then bulk brain |
| Vasculature cells | Matched endothelial/pericyte subtype | Vascular aggregate, then bulk brain |

An oligodendrocyte result is not exact OPC evidence, and a bulk-brain result is not cell-type replication.

### 5.3 Primary statistical rules

Use the following as project-level working rules and retain the continuous statistics:

- genome-wide significance for common-variant discovery: `P < 5e-8`;
- study-wide correction for gene burden: use the threshold reported by the study, including masks tested;
- primary colocalization support: `PP.H4 >= 0.80` and `PP.H4 / (PP.H3 + PP.H4) >= 0.80`;
- strong colocalization must also survive reasonable prior sensitivity, pass locus QC, and account for multiple signals when present;
- for a direct coding/splice route, use `variant PIP >= 0.50` in a well-QC'd credible set as the working strong-evidence threshold; retain the exact PIP, credible-set coverage, and competing variants;
- `0.50 <= PP.H4 < 0.80` is suggestive, not strong; and
- never convert a posterior threshold into a claim of mediation or causality.

The conditional H4 value is undefined when `PP.H3 + PP.H4` is effectively zero. Store it as missing rather than forcing a value.

### 5.4 Direction convention

After allele harmonization:

```text
GWAS beta > 0: the effect allele increases AD risk
QTL beta  > 0: the same effect allele increases expression or molecular trait value
```

Then `sign(GWAS beta × QTL beta) > 0` means that the allele increasing the molecular trait is associated with higher AD risk. A negative product means that it is associated with lower risk. This is an allele-direction description, not proof that changing gene expression will change AD risk.

Do not declare agreement with a Phase 18 DEG direction unless the biological contrast and direction are genuinely comparable. KDA selection alone does not predict the sign of a causal expression effect.

## 6. Build the candidate-locus table

Create `phase18_wp5_candidate_loci.tsv` with:

```text
key_driver
ensembl_gene_id
approved_symbol
chromosome
gene_start_grch38
gene_end_grch38
strand
tss_grch38
screen_start_grch38
screen_end_grch38
is_mtdna_gene
coordinate_source
coordinate_source_version
retrieval_date
```

Rules:

1. Resolve aliases to an approved symbol and stable Ensembl gene ID.
2. Use GRCh38 as the internal coordinate system because the current FunGen-AD resources are harmonized to GRCh38.
3. For the initial catalog screen, use the gene body plus 1 Mb on each side, bounded at position 1. This is a discovery window, not evidence that every variant in the window regulates the gene.
4. For formal fine mapping or colocalization, use the complete fine-mapping/LD block or the QTL study's prespecified cis region, not an arbitrary gene window that cuts through a signal.
5. Record transcript choice only when interpreting coding/splicing consequences. Prefer a documented MANE transcript where available, but retain all relevant consequences.
6. Treat the APOE region separately. The current FunGen-AD resource identifies GRCh38 chr19:44.4-46.5 Mb as a special region because of its complex LD.

A credible set contains variants, not genes. Write “a credible-set variant was mapped to gene X by ...,” not “gene X was in the credible set.”

## 7. Register and obtain the evidence sources

### 7.1 Resource priority

Use resources in this order:

1. **FunGen-AD precomputed results:** harmonized AD GWAS fine mapping and AD-molecular-QTL colocalization.
2. **Full GWAS and QTL summary statistics:** for custom locus QC or reruns.
3. **NIAGADS Alzheimer's GenomicsDB/ADVP and GWAS Catalog:** discovery and cross-checking.
4. **Published or approved ADSP sequencing analyses:** rare variants and gene burden.

The current [FunGen-AD AD GWAS page](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/gwas/AD_GWAS/) describes GRCh38 harmonization, the ADSP European-ancestry LD panel, and downloadable fine-mapping results. Its [eQTL](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/eQTL/), [sQTL](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/sQTL/), and [caQTL](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/caQTL/) pages list QTL fine-mapping and AD colocalization outputs.

The [GWAS Catalog documentation](https://www.ebi.ac.uk/gwas/docs/faq) explains that the visible curated associations are a significance-filtered subset; use full summary statistics for regional analysis. NIAGADS provides an [open-access discovery layer](https://www.niagads.org/open-access/) and a separate [Data Sharing Service](https://dss.niagads.org/) for open and controlled datasets.

### 7.2 Dataset registry

Before extracting candidate results, populate `phase18_wp5_dataset_registry.tsv`:

```text
dataset_id
resource
study_accession
publication_doi_or_pmid
phenotype
phenotype_tier
case_definition
ancestry
n_total
n_cases
n_controls
brain_region
cell_type
qtl_type
genome_build
variant_id_scheme
effect_allele_definition
summary_stats_complete
beta_available
se_available
eaf_or_maf_available
imputation_info_available
ld_reference
sample_overlap_notes
access_class
source_url_or_synapse_id
file_version
file_checksum
retrieval_date
eligible_primary
exclusion_reason
```

Do not infer ancestry, build, sample size, or allele convention from a filename.

### 7.3 Synapse inventory and download

The currently documented FunGen-AD resources include:

```text
syn69696846  AD fine-mapping results
syn69865824  top-locus unified fine-mapping summary
syn69865816  AD-molecular-QTL colocalization results
syn69670630  AD-molecular-QTL colocalization models
syn69670592  molecular-QTL fine-mapping models/results
syn69670652  ADSP European-ancestry LD reference
```

IDs and permissions can change. Inventory each container and record the exact child file ID/version before downloading. With the [Synapse command-line client](https://python-docs.synapse.org/en/stable/tutorials/command_line_client/), the pattern is:

```bash
synapse list syn69865816
synapse list syn69696846

synapse get SYNAPSE_FILE_ID \
  --downloadLocation /approved/data/path/phase18_wp5
```

Use recursive download only after checking container size and contents:

```bash
synapse get -r SYNAPSE_FOLDER_ID \
  --downloadLocation /approved/data/path/phase18_wp5
```

Authenticate without putting a token in a script, notebook, shell history, or repository. Accept the applicable Synapse data-use terms. Record file entity ID, version, checksum, and download date.

The [NIAGADS open-access API](https://api.niagads.org/docs/introduction/niagads-open-access) is currently marked as under development. It is useful for discovery, but the primary reproducible analysis should pin downloaded files rather than depend on unstable API responses.

## 8. Stage A: common-variant and fine-mapping screen

Perform this once per candidate gene.

### 8.1 Catalog screen

For the approved symbol, aliases, gene interval, and any known lead variants:

1. search NIAGADS Alzheimer's GenomicsDB;
2. search the NHGRI-EBI GWAS Catalog by gene, region, trait, and variant;
3. search the registered AD-related phenotypes, not every available trait;
4. export or save the result snapshot; and
5. record the search date and query.

For every potentially relevant association, capture:

```text
candidate
phenotype
study_accession
publication
ancestry
n_cases
n_controls
lead_variant
effect_allele
other_allele
beta_or_odds_ratio
standard_error_or_ci
p_value
genome_build
distance_to_gene
catalog_mapped_gene
mapping_basis
```

The Catalog's mapped or nearest gene is not itself evidence that the gene mediates the association.

### 8.2 Fine-mapping extraction

For every GWAS locus overlapping the screen window:

1. identify the complete locus/block used by the source;
2. extract all credible sets and independent signals, not only the lead variant;
3. record credible-set coverage, purity, variant PIP, method, ancestry, and LD source;
4. annotate credible-set variants against GRCh38 transcripts and regulatory features;
5. determine whether any variant has a direct coding consequence in the candidate; and
6. retain credible mappings to other genes to avoid candidate-confirmation bias.

Required fields in `phase18_wp5_common_variant_evidence.tsv` include:

```text
key_driver
study_accession
phenotype
ancestry
locus_id
signal_id
credible_set_id
credible_set_coverage
credible_set_purity
variant_id
chr_grch38
pos_grch38
ref
alt
effect_allele
gwas_beta
gwas_se
gwas_p
variant_pip
functional_consequence
consequence_transcript
mapped_gene
mapping_category
mapping_evidence
source_file
source_version
```

Use controlled mapping categories:

```text
coding_candidate
splice_candidate
promoter_candidate
enhancer_candidate
colocalized_eqtl_candidate
colocalized_sqtl_candidate
caqtl_regulatory_chain_candidate
nearest_gene_only
mapped_to_other_gene
unresolved
```

### 8.3 Interpretation

- A high-PIP protein-altering variant in the candidate is direct gene-level evidence.
- A non-coding credible-set variant needs functional mapping or colocalization.
- Physical overlap with the gene body is not enough.
- A lead variant outside the gene can support it if a credible regulatory/QTL chain connects them.
- If the locus has multiple plausible genes, report that ambiguity.

## 9. Stage B: use precomputed AD-QTL colocalization first

This is the preferred first-pass molecular mechanism analysis because the current FunGen-AD release already harmonizes its GWAS/QTL inputs and performs fine mapping.

For each `candidate × context × QTL type × GWAS`:

1. match the candidate by stable Ensembl gene ID; strip a version suffix only after confirming the resource convention;
2. filter to eQTL and sQTL results first;
3. prioritize the exact Phase 18 cell type using Section 5.2;
4. retain bulk brain and other brain regions as secondary evidence;
5. capture every independent signal pair rather than only the largest posterior;
6. record the colocalization method and hypotheses/posteriors exactly as supplied;
7. verify that both GWAS and QTL have a detectable regional signal;
8. inspect the locus and credible-set overlap; and
9. calculate the harmonized allele-direction statement when effect estimates are available.

Use caQTL as a mechanistic bridge. The strongest non-coding chain is:

```text
AD GWAS signal
  ↕ colocalization
cell-type caQTL
  ↕ colocalization or fine-mapped overlap
candidate eQTL/sQTL
```

An AD-caQTL result alone identifies a cell-type regulatory element; it does not identify the candidate gene unless the peak-to-gene connection is supported.

TWAS/qTWAS/cTWAS may be recorded as supplementary evidence. A TWAS association alone is not a substitute for colocalization because LD and correlated predicted expression can implicate the wrong gene.

## 10. Stage C: harmonize full summary statistics for a custom rerun

Run this stage only if the precomputed result is missing, methodologically unsuitable, or requires a transparent sensitivity analysis.

### 10.1 Minimum input fields

For GWAS and QTL in the complete regional window, obtain:

```text
chromosome
position
effect_allele
other_allele
beta
standard_error
p_value
variant_id
effect_allele_frequency or MAF
imputation quality, if available
sample size
```

For a case-control GWAS, also obtain the case fraction. For a quantitative QTL, obtain the phenotype standard deviation or enough information for the method to estimate it.

P-value-only data are inadequate for a primary directional colocalization analysis. If only P value, MAF, and sample size are available, `coloc` can approximate Bayes factors, but label the result as a sensitivity analysis.

### 10.2 Variant normalization

1. Convert both datasets to the same genome build, preferably GRCh38.
2. Split multiallelic records and left-normalize indels against the correct reference genome.
3. Use `chromosome:position:ref:alt` as the internal key; retain rsIDs as annotations.
4. Verify the reference allele after any lift-over. Drop variants that fail reference validation.
5. Align both studies to the same effect allele.
6. Flip beta when effect and other alleles are swapped.
7. Resolve strand-ambiguous A/T and C/G variants with allele frequencies. Drop them if orientation remains uncertain.
8. Exclude allele mismatches and record their count/reason.
9. Do not filter the shared locus to significant variants. Colocalization requires dense regional coverage.

### 10.3 Default variant QC before matching

Use each study's primary QC first. A defensible minimum validation before matching is:

```text
imputation INFO >= 0.8
biallelic variants
valid allele frequency with the source study's prespecified MAF/MAC filter satisfied
finite beta, SE, and P
SE > 0
0 < P <= 1
```

Do not impose a new post hoc MAF or P-value filter on the matched locus. If an LD panel is unreliable below a frequency threshold, define that limitation before analysis and apply it consistently. Report counts before QC, after QC, and after cross-study matching.

### 10.4 Locus assessability QC

Call a candidate-QTL pair assessable only when:

- both studies cover the complete locus densely;
- the lead/credible variants from both signals survive harmonization;
- effect alleles are unambiguous;
- the relevant gene or splice phenotype was actually tested;
- sample size and trait type are known;
- the LD source, if needed, matches ancestry and genome build; and
- regional plots show no obvious truncation or coordinate error.

Record:

```text
n_gwas_variants_raw
n_qtl_variants_raw
n_shared_variants
shared_fraction_of_smaller_dataset
gwas_lead_present
qtl_lead_present
n_allele_flips
n_ambiguous_dropped
n_mismatch_dropped
minimum_gwas_p
minimum_qtl_p
regional_signal_status
assessable
failure_reason
```

Do not label a missing QTL, unmeasured gene, sparse overlap, or absent effect sizes as “no colocalization.” Use `not_assessable`.

## 11. Stage D: custom colocalization

### 11.1 Choose the method

Use:

- `coloc.susie` when dense summary statistics and suitable LD are available and the region may have multiple causal signals;
- `coloc.abf` only when a single-causal-variant assumption is defensible, or as a prespecified sensitivity analysis; or
- the FunGen-xQTL precomputed fine-mapping/colocalization outputs when the required raw inputs or matched LD are unavailable.

The current [`coloc` data guide](https://chr1swallace.github.io/coloc/articles/a02_data.html) requires dense coverage of one region and warns against P-value filtering. Its [SuSiE guide](https://chr1swallace.github.io/coloc/articles/a06_SuSiE.html) recommends `runsusie` followed by `coloc.susie` when multiple causal variants are possible.

### 11.2 R template for a single-signal analysis

Assume `gwas` and `qtl` have already been harmonized into one row per shared variant and both betas refer to the same effect allele.

```r
library(data.table)
library(coloc)

x <- fread("harmonized/CANDIDATE__CONTEXT__GWAS__QTL.tsv.gz")

stopifnot(
  !anyDuplicated(x$variant_id),
  all(is.finite(x$gwas_beta)),
  all(is.finite(x$gwas_se) & x$gwas_se > 0),
  all(is.finite(x$qtl_beta)),
  all(is.finite(x$qtl_se) & x$qtl_se > 0)
)

d_gwas <- list(
  beta = x$gwas_beta,
  varbeta = x$gwas_se^2,
  snp = x$variant_id,
  position = x$pos_grch38,
  type = "cc",
  N = GWAS_N_TOTAL,
  s = GWAS_N_CASES / GWAS_N_TOTAL
)

d_qtl <- list(
  beta = x$qtl_beta,
  varbeta = x$qtl_se^2,
  snp = x$variant_id,
  position = x$pos_grch38,
  type = "quant",
  N = QTL_N,
  MAF = x$qtl_maf
)

check_dataset(d_gwas)
check_dataset(d_qtl)
plot_datasets(d_gwas, d_qtl)

fit <- coloc.abf(
  dataset1 = d_gwas,
  dataset2 = d_qtl,
  p1 = 1e-4,
  p2 = 1e-4,
  p12 = 5e-6
)

print(fit$summary)
sensitivity(fit, rule = "H4 > 0.8 & H4 > 4*H3")
```

Do not set `sdY = 1` for the QTL merely for convenience. Use it only if the molecular phenotype was truly standardized to variance 1; otherwise supply `N` and `MAF`, as shown, or the correct phenotype standard deviation.

### 11.3 R template for multiple signals

Construct a separate, allele-aligned LD matrix for each study when their ancestry or samples differ. Row and column names must exactly match the variant IDs and order in the corresponding dataset.

```r
d_gwas$MAF <- x$gwas_maf
d_gwas$LD <- gwas_ld[x$variant_id, x$variant_id]
d_qtl$LD <- qtl_ld[x$variant_id, x$variant_id]

check_dataset(d_gwas, req = "LD")
check_dataset(d_qtl, req = "LD")

check_alignment(d_gwas)
check_alignment(d_qtl)

gwas_susie <- runsusie(d_gwas)
qtl_susie <- runsusie(d_qtl)

fit_susie <- coloc.susie(
  gwas_susie,
  qtl_susie,
  p1 = 1e-4,
  p2 = 1e-4,
  p12 = 5e-6
)

print(fit_susie$summary)
```

Requirements:

- use in-sample LD when allowed and available;
- otherwise use ancestry-matched reference LD;
- do not use the FunGen-AD European LD panel for a non-European analysis;
- make beta allele orientation consistent with the LD allele coding;
- require SuSiE convergence and inspect credible-set purity; and
- report every GWAS-signal × QTL-signal pair.

### 11.4 Prior and locus sensitivity

At minimum, rerun the shared-variant prior across:

```text
p12 = 1e-6
p12 = 5e-6
p12 = 1e-5
```

Also check a defensible alternative locus definition, such as the source fine-mapping block versus the full QTL cis window. Do not search many windows or priors and report only the favorable result.

For each result store all five hypotheses:

| Hypothesis | Interpretation |
|---|---|
| H0 | Neither trait is associated in the region |
| H1 | GWAS only |
| H2 | QTL only |
| H3 | Both associated, different causal signals |
| H4 | Both associated, shared causal signal |

High H1/H2 means the pair is poorly powered for colocalization, not evidence for distinct mechanisms. High H3 supports two regional signals that do not appear shared. High H4 supports a shared signal, not proven mediation.

### 11.5 Colocalization output schema

`phase18_wp5_colocalization.tsv` should include:

```text
key_driver
broad_network
ensembl_gene_id
qtl_type
molecular_trait_id
qtl_context
context_match_level
brain_region
gwas_dataset
gwas_phenotype
ancestry_gwas
ancestry_qtl
locus_id
gwas_signal_id
qtl_signal_id
method
n_shared_variants
pp_h0
pp_h1
pp_h2
pp_h3
pp_h4
pp_h4_given_h3h4
top_shared_variant
top_shared_variant_posterior
gwas_beta_effect_allele
qtl_beta_same_allele
allele_direction_statement
prior_p1
prior_p2
prior_p12
prior_sensitivity_pass
multiple_signals_accounted
ld_source_gwas
ld_source_qtl
assessable
qc_status
source_file_or_model
```

## 12. Stage E: rare-variant and coding evidence

### 12.1 Published/summary-result route

For each candidate:

1. search the ADSP publication index, NIAGADS resources, PubMed, and paper supplements for gene-level AD/ADRD sequencing results;
2. verify that the candidate was tested, not merely discussed;
3. distinguish a single variant test from a gene burden/SKAT-O/STAAR test;
4. record the exact annotation mask and allele-frequency cutoff;
5. record ancestry, sample size, phenotype, covariates, relatedness handling, and sequencing platform;
6. record the number of genes and masks tested and the corrected threshold;
7. determine whether evidence was replicated in an independent cohort; and
8. inspect whether one variant entirely drives an aggregate result.

Required fields in `phase18_wp5_rare_variant_evidence.tsv`:

```text
key_driver
study_accession_or_publication
phenotype
ancestry
n_total
n_cases
n_controls
sequencing_type
test_unit
test_method
variant_mask
annotation_definition
maf_threshold
minimum_mac
n_variants_in_test
cumulative_mac
effect_estimate
standard_error
p_value
corrected_threshold
passes_study_wide_correction
replication_status
conditioning
single_variant_driver
quality_notes
source
```

The presence of rare variants in AD cases is not an association. Case-only carrier counts, ClinVar classifications, or damaging-prediction scores do not establish AD risk.

### 12.2 Optional de novo ADSP analysis

Only undertake a new individual-level WES/WGS analysis if the team has approved NIAGADS access, an analysis plan covered by the data-use agreement, and enough samples/events for useful power. The current ADSP site directs genomic data access through [NIAGADS DSS](https://adsp.niagads.org/), and the [ADSP discovery portal](https://adsp.niagads.org/niagads-data-discovery-portal-via-gen3/) can be used to inspect cohort/data availability before applying.

Prespecify:

- diagnosis and age filters;
- ancestry-stratified analyses and meta-analysis plan;
- sample relatedness and duplicate removal;
- genotype/variant QC;
- coverage/callability masks;
- principal components and technical covariates;
- two or more biologically justified masks, such as high-confidence predicted loss-of-function and damaging missense;
- MAF/MAC thresholds;
- a burden test plus a variance-component or combined test;
- study-wide correction across genes and masks;
- primary and APOE-adjusted sensitivity models; and
- an independent replication strategy.

Use a rare-variant method appropriate for unbalanced case-control data and related samples. Do not choose the method or mask after seeing which one produces the smallest P value.

## 13. Evidence grading and final integration

### 13.1 Assessability first

Assign each evidence route one status:

```text
positive
no_shared_signal
distinct_signals
no_regional_signal
not_assessable
not_searched
```

Examples:

- gene absent from the QTL assay: `not_assessable`;
- good signals in both traits with high H3 and low H4: `distinct_signals`;
- adequate dense data with QTL signal but no GWAS regional signal: `no_regional_signal`;
- no relevant result in the sources actually searched: no positive evidence, with the sources/date retained.

### 13.2 Candidate-context grade

| Grade | Required evidence |
|---|---|
| Strong | A well-fine-mapped coding/splice variant directly implicating the candidate; a robust AD-candidate eQTL/sQTL colocalization with strong locus QC and preferably matched cell type; or a corrected replicated rare-variant gene association |
| Moderate | Several convergent mappings from an AD credible set to the candidate; corrected but not yet replicated rare-variant evidence; or convincing colocalization in a relevant but non-matched tissue/context |
| Weak | Nearest-gene assignment, gene-body overlap alone, TWAS alone, suggestive/nominal association, uncorrected burden, or an incomplete regulatory chain |
| None found | No convincing evidence in the explicitly searched and assessable sources |

Use the strongest qualifying grade, but retain contradictory evidence and ambiguity. Add separate flags for `context_matched`, `replicated`, and `conflicting_evidence`; do not hide these inside the grade.

APOE is a positive control and should not calibrate thresholds. The APOE region's complex LD and very large effect require separate handling rather than treating it as an ordinary locus.

### 13.3 Final summary table

`phase18_human_genetic_evidence.tsv` should contain:

```text
key_driver
broad_network
ensembl_gene_id
common_variant_status
best_gwas_phenotype
best_gwas_study
best_locus_id
best_mapping_category
best_variant
best_variant_pip
coding_support
best_eqtl_coloc_pp_h4
best_sqtl_coloc_pp_h4
best_matched_cell_type_coloc_pp_h4
best_coloc_method
best_coloc_context
best_coloc_direction
caqtl_regulatory_chain
twas_support
rare_variant_status
rare_variant_best_p
rare_variant_corrected
rare_variant_replicated
genetic_evidence_grade
context_matched
conflicting_evidence
assessability_summary
interpretation
source_ids
analysis_version
analysis_date
```

For fields with “best,” use the prespecified phenotype and context hierarchy, then the strongest methodologically valid evidence. Do not select solely by the smallest P value or largest H4.

## 14. Multiple testing, replication, and independence

- Catalog lookup is descriptive; do not reinterpret a nominal catalog association as corrected because only six candidates were searched.
- For published GWAS and gene-burden results, retain the original study-wide correction.
- Colocalization posteriors are not P values, but testing many genes, QTL phenotypes, tissues, and GWAS still increases the opportunity for favorable results. Separate the frozen primary comparisons from exploratory comparisons.
- Treat correlated QTL cell types/brain regions from the same donors as correlated evidence.
- Treat multiple GWAS meta-analyses with overlapping cohorts as sensitivity analyses, not independent replication.
- A second platform or analysis of substantially the same people is not a fully independent replication cohort.
- Report candidate failure and unassessability as carefully as positive results.

## 15. Special workflow for mitochondrial DNA genes

Standard nuclear cis-GWAS/eQTL logic is often inappropriate for `MT-*` candidates. For every mtDNA-encoded candidate, add a mitochondrial-specific evidence track:

1. mtDNA single-nucleotide and indel associations;
2. heteroplasmy level and heteroplasmy burden;
3. mtDNA haplogroup;
4. mtDNA copy number;
5. tissue-specific versus blood-derived measurements; and
6. nuclear variants regulating mitochondrial copy number, transcription, translation, or maintenance.

Record:

```text
mitochondrial_reference_build
mt_position
ref
alt
heteroplasmy_threshold
read_depth
tissue
haplogroup_adjustment
NUMT_handling
copy_number_method
batch_adjustment
ancestry
```

Do not assign a genome-wide mtDNA copy-number association to one mitochondrial gene. Do not use a standard nuclear LD panel for mtDNA colocalization. Be alert to nuclear mitochondrial DNA segments (NUMTs), low read depth, tissue-dependent heteroplasmy, and platform effects.

## 16. Required QC and stopping rules

### Candidate and resource QC

- [ ] Candidate list and contexts exactly match the frozen WP1 manifest.
- [ ] Approved symbol and stable Ensembl ID are resolved.
- [ ] All coordinates use a recorded build.
- [ ] Dataset accession, version, checksum, phenotype, ancestry, and sample size are recorded.
- [ ] Cohort overlap is documented.
- [ ] Primary versus secondary phenotypes and contexts were frozen before extraction.

### Fine-mapping QC

- [ ] All signals and credible sets in the locus were examined.
- [ ] Variant PIP is not confused with gene probability.
- [ ] Coding/splicing consequence uses a documented transcript.
- [ ] Non-coding mapping includes an explicit evidence chain.
- [ ] Other plausible genes at the locus remain visible.

### Colocalization QC

- [ ] Both traits use dense, complete regional statistics.
- [ ] Build and alleles are harmonized.
- [ ] Ambiguous/mismatched variants and lead-variant retention are reported.
- [ ] Both regional association strengths were checked.
- [ ] Multiple signals were handled or a limitation is stated.
- [ ] LD is ancestry/build/allele matched.
- [ ] All H0-H4 posteriors are reported.
- [ ] Priors and locus definition were tested.
- [ ] Exact cell-type match versus fallback is labeled.
- [ ] Effect direction uses the same effect allele.

### Rare-variant QC

- [ ] The gene was actually tested.
- [ ] Mask, MAF, MAC, method, and correction are recorded.
- [ ] Case-only observation is not called association.
- [ ] A one-variant-driven burden is disclosed.
- [ ] Ancestry and replication are explicit.

Stop and label the comparison `not_assessable` when effect alleles/build cannot be resolved, the candidate was not measured/tested, locus coverage is sparse, required metadata are missing, or suitable LD is unavailable for the intended multi-signal method. Do not repair these failures by switching to a favorable nearby result.

## 17. Figures

Produce:

1. a candidate × evidence heatmap showing common coding, matched-cell eQTL, sQTL, regulatory-chain, TWAS-only, and rare-variant evidence separately;
2. a locus plot for every strong or moderate colocalization, displaying both GWAS and QTL association patterns and credible sets; and
3. an allele-direction forest/table for supported QTL mechanisms.

Use a distinct symbol for `not_assessable`; do not display it as zero evidence. APOE can dominate plot scales, so show it in a separate panel or use an appropriate scale without hiding the other candidates.

## 18. Wording for the manuscript

Acceptable:

> The AD association and the astrocyte eQTL for X showed evidence of a shared regional signal (PP.H4 = ..., prespecified prior), supporting X as a candidate effector gene at this locus. Colocalization does not by itself establish mediation.

> X was the nearest gene to the lead variant, but fine mapping and molecular-QTL analyses did not specifically implicate X; this was graded as weak support.

> No convincing genetic support for X was found in the prespecified sources. This does not exclude a disease-relevant trans-acting or context-dependent role.

Avoid:

```text
X is an AD gene because it is near a GWAS SNP.
X is causal because H4 is high.
X is mutated in AD patients.
The absence of a GWAS signal proves X is not involved in AD.
```

## 19. Completion criteria

WP5 is complete for the pilot when:

- all six genes and all frozen pilot contexts have an assessability record;
- common-variant/fine-mapping evidence has been screened with explicit mapping categories;
- matched-cell-type eQTL and sQTL colocalization has been queried wherever available;
- every custom colocalization has full harmonization, locus, LD, posterior, and sensitivity QC;
- rare-variant evidence has been searched with the exact masks/correction recorded;
- `phase18_human_genetic_evidence.tsv` and all supporting audit tables exist;
- strong/moderate results have inspectable locus plots; and
- the written interpretation distinguishes shared signal, gene mapping, mediation, and causality.

## 20. Resource and method references

- [FunGen-AD AD GWAS summary statistics, fine mapping, and LD resources](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/gwas/AD_GWAS/)
- [FunGen-AD eQTL resources and AD colocalization outputs](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/eQTL/)
- [FunGen-AD sQTL resources and AD colocalization outputs](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/sQTL/)
- [FunGen-AD cell-type caQTL resources](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/caQTL/)
- [NIAGADS open-access resources](https://www.niagads.org/open-access/)
- [NIAGADS Data Sharing Service](https://dss.niagads.org/)
- [ADSP data and publications](https://adsp.niagads.org/)
- [NHGRI-EBI GWAS Catalog access and summary-statistics guidance](https://www.ebi.ac.uk/gwas/docs/faq)
- [`coloc` data requirements](https://chr1swallace.github.io/coloc/articles/a02_data.html)
- [`coloc.susie` workflow for multiple signals](https://chr1swallace.github.io/coloc/articles/a06_SuSiE.html)
- [FunGen-xQTL pairwise enrichment and colocalization protocol](https://statfungen.github.io/xqtl-protocol/SuSiE_enloc.html)
- Giambartolomei C, et al. Bayesian test for colocalisation between pairs of genetic association studies using summary statistics. *PLoS Genetics*. 2014. [doi:10.1371/journal.pgen.1004383](https://doi.org/10.1371/journal.pgen.1004383)
- Wallace C. A more accurate method for colocalisation analysis allowing for multiple causal variants. *PLoS Genetics*. 2021. [doi:10.1371/journal.pgen.1009440](https://doi.org/10.1371/journal.pgen.1009440)
