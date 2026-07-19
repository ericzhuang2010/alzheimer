# Phase 09 Extended-Tier Reference Acquisition Plan

## Status and decision

This document defines how to acquire, freeze, validate, and integrate the
optional extended mitochondrial reference used by Phase 09 on the local
machine.

Local reference acquisition was completed and validated on `2026-07-18`.
The four-file reference bundle is ready. Phase 09 configuration and script
integration remain pending because `config/phase09_annotation.yml` and
`scripts/09_annotate_mitochondrial_genes.R` have not yet been implemented.

The selected reference is a prespecified four-pathway panel from Reactome
V97. It represents mitochondrial regulators and stress-response machinery
that need not be permanently localized in mitochondria.

Use these pathways:

| Reactome stable ID | Pathway | Total genes | MitoCarta overlap | Extended-only genes | Review status |
|---|---|---:|---:|---:|---:|
| `R-HSA-1592230` | Mitochondrial biogenesis | 95 | 50 | 45 | 5/5 |
| `R-HSA-5205647` | Mitophagy | 39 | 17 | 22 | 5/5 |
| `R-HSA-9840373` | Cellular response to mitochondrial stress | 9 | 5 | 4 | 5/5 |
| `R-HSA-9841251` | Mitochondrial unfolded protein response (UPRmt) | 18 | 8 | 10 | 3/5 |
| **Union** | Four-pathway panel | **157** | **77** | **80** | — |

Counts were calculated after normalizing Reactome and MitoCarta symbols
through the frozen HGNC `2026-06-05` snapshot. Overlap counts are not
additive because genes can belong to more than one pathway.

All 80 extended-only genes occur in the local Vasculature Phase 03 feature
universe. Seventy-seven are test-eligible; `DEFA5`, `PRKAG3`, and
`UBE2V1` are present but not currently test-eligible.

The UPRmt pathway is released but has Reactome review status 3/5: it has been
internally reviewed and awaits renewed external review following structural
revision. Retain that status in provenance and continue to treat the complete
extended tier as secondary/sensitivity evidence.

## Scientific role and classification

The panel covers:

- upstream regulation of mitochondrial biogenesis;
- general autophagy machinery specifically recruited during mitophagy;
- cytosolic integrated-stress signaling triggered by mitochondrial damage;
- nuclear transcriptional responses to mitochondrial protein-folding stress.

The authoritative GMT must retain all 157 pathway participants. Phase 09 then
applies this classification precedence:

1. MitoCarta3.0 member -> `core_mito_protein`;
2. mtDNA rRNA or tRNA -> `mtdna_noncoding`;
3. member of the Reactome panel but not an earlier tier -> `mito_extended`;
4. otherwise -> `non_mito`.

Do not remove the 77 MitoCarta members from the GMT. Removing them would
distort pathway membership. The set difference is applied only to
`mito_tier`, after HGNC normalization and MitoCarta classification.

## Alternatives investigated

### Gene Ontology

A five-root GO biological-process panel was evaluated using GO release
`2026-06-15` and the human UniProt GAF generated `2026-06-18`.

| Evidence policy | Union genes | Extended-only genes |
|---|---:|---:|
| All evidence | 430 | 187 |
| Excluding `IEA` | 416 | 175 |
| Experimental evidence only | 297 | 112 |

The GO result changes materially with the evidence policy, and the current GO
UPRmt term has only two annotated genes. GO is therefore suitable for a later
sensitivity analysis, but not as the primary extended classifier.

### MSigDB

MSigDB republishes many of the same Reactome and GO sets, adds another
licensing/versioning layer, and its Reactome collection can lag the current
Reactome release. It provides no scientific advantage over freezing the
primary Reactome source directly.

### MitoMiner/IMPI

MitoMiner/IMPI primarily compiles or predicts mitochondrial protein
localization. That overlaps the purpose of MitoCarta rather than identifying
indirect regulators and stress machinery.

### Other Reactome pathways

- Mitochondrial calcium ion transport contains 23 genes but adds only one
  non-MitoCarta gene after HGNC normalization, so it is largely redundant.
- The intrinsic apoptosis pathway adds 39 non-MitoCarta genes, but many are
  generic apoptosis and signaling genes. It is too broad for
  `mito_extended`.

## Frozen source specification

Use the version-specific Reactome V97 URL, never the mutable `current` URL:

```text
https://reactome.org/download/97/ReactomePathways.gmt.zip
```

Reactome V97 was released in June 2026. Reactome annotation files are
distributed as CC0 data.

Frozen checksums:

| Artifact | SHA-256 |
|---|---|
| `ReactomePathways.v97.gmt.zip` | `8c1dbc8578431da5d2d5118262718c60b553a9be3398e93658daa069e4a9afd4` |
| Extracted full `ReactomePathways.v97.gmt` | `89983d5c1f0af11c52edfeee7323eb425580ac6281d387a528562ab1787ce56b` |
| Derived four-pathway `mitochondrial_extended_gene_sets.gmt` | `f4d8b6c7a74894929028805e5e3cf81523968f8eecc380ac52b47038c5f9b847` |
| Generated `mitochondrial_extended_manifest.tsv` | `8d77d6782872d6d19eb98a6297c92dda686dfba719199c6c0b6346d4127fb4ec` |

The version-specific ZIP was verified to be byte-identical to the Reactome
`current` download available during this investigation.

## Inputs

| Input | Role |
|---|---|
| Reactome V97 pathway GMT ZIP | Primary source for the four selected pathway definitions |
| `data/reference/Human.MitoCarta3.0.xls` | Core-tier precedence and overlap validation |
| `data/reference/hgnc/hgnc_complete_set_2026-06-05.txt` | Current-symbol, previous-symbol, alias, Entrez, and Ensembl normalization |
| Phase 03 tested-gene universe | RDS-specific presence and test-eligibility validation |

The download and filtering operation must not read Phase 08 DEG results.
Selection is reference-driven and frozen before inspecting annotated DEGs.

## End state

When this plan is complete, Phase 09 has one locally frozen Reactome V97
extended-tier reference bundle, the extended tier is enabled in its dedicated
configuration, and the annotation script validates and uses the bundle without
altering Phase 08 results or statistics.

The scientific end state is:

- four complete Reactome pathway sets with 157 unique source symbols;
- 77 HGNC-normalized members retained as `core_mito_protein` because they are
  already in MitoCarta3.0;
- 80 non-core members classified as `mito_extended`;
- all one-to-many pathway memberships retained;
- provenance and validation status recorded for every reference artifact.

### Reference files added

Create these files under:

```text
data/reference/mitochondrial_extended/
```

| File | Contents |
|---|---|
| `ReactomePathways.v97.gmt.zip` | Unmodified official Reactome V97 source archive |
| `ReactomePathways.v97.gmt` | Unmodified GMT extracted from the official ZIP |
| `mitochondrial_extended_gene_sets.gmt` | Exactly four selected V97 pathway rows, retaining all 157 source symbols |
| `mitochondrial_extended_manifest.tsv` | Source, version, release, license, pathway IDs, review status, counts, selection rule, and checksums |

The source and derived files are ignored by Git because they are under
`data/`.

### Repository files added or changed

| File | End-state change |
|---|---|
| `docs/phase_09_annotate_genes/phase_09_extended_tier_reference_plan.md` | This local acquisition, integration, and validation plan is added. |
| `config/phase09_annotation.yml` | Add `extended_tier.enabled: true`, the four stable IDs, paths, versions, and frozen checksums. |
| `scripts/09_annotate_mitochondrial_genes.R` | Add reference/hash validation, HGNC normalization, MitoCarta precedence, long pathway membership, and `mito_extended` assignment. |
| `docs/phase_09_annotate_genes/phase_09_annotate_mitochondrial_genes_plan.md` | Update the Phase 09 implementation checklist to record that the extended tier is configured and frozen. |

The last three changes occur during Phase 09 implementation. The download
step adds the ZIP; completing the local extraction, filtering, and provenance
steps produces the four-file reference bundle under
`data/reference/mitochondrial_extended/`.

### Files that remain unchanged

This work does not change:

- `config/analysis_parameters.yml`;
- `scripts/08_run_mast.R` or any other Phase 08 script;
- any Phase 00–08 result or status file;
- the frozen MitoCarta workbook;
- the frozen HGNC snapshot;
- archived Phase 09–15 code or results;
- anything under `results/figures/`.

No new result file is created until Phase 09 itself is executed. Phase 09
outputs remain those defined in
`phase_09_annotate_mitochondrial_genes_plan.md` under
`results/<environment>/09_annotate_genes/`.

## Local acquisition and construction

### Prerequisites

Run from the repository root and confirm the required tools and frozen inputs:

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer

command -v wget
command -v unzip
command -v sha256sum
command -v Rscript

test -r data/reference/Human.MitoCarta3.0.xls
test -r data/reference/hgnc/hgnc_complete_set_2026-06-05.txt
```

### Step 1: create the reference directory

```bash
mkdir -p data/reference/mitochondrial_extended
```

Before downloading, stop if a file with the frozen name already exists. Do
not overwrite an existing reference without investigating it.

```bash
test ! -e data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.zip
test ! -e data/reference/mitochondrial_extended/ReactomePathways.v97.gmt
test ! -e data/reference/mitochondrial_extended/mitochondrial_extended_gene_sets.gmt
test ! -e data/reference/mitochondrial_extended/mitochondrial_extended_manifest.tsv
```

### Step 2: download and validate the immutable V97 archive

```bash
wget \
  -O data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.zip.part \
  https://reactome.org/download/97/ReactomePathways.gmt.zip

printf '%s  %s\n' \
  '8c1dbc8578431da5d2d5118262718c60b553a9be3398e93658daa069e4a9afd4' \
  'data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.zip.part' | \
  sha256sum --check --strict

mv \
  data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.zip.part \
  data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.zip
```

If checksum validation fails, do not rename or use the partial file.

### Step 3: extract and validate the full source GMT

```bash
unzip -p \
  data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.zip \
  ReactomePathways.gmt \
  > data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.part

printf '%s  %s\n' \
  '89983d5c1f0af11c52edfeee7323eb425580ac6281d387a528562ab1787ce56b' \
  'data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.part' | \
  sha256sum --check --strict

mv \
  data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.part \
  data/reference/mitochondrial_extended/ReactomePathways.v97.gmt
```

### Step 4: select exactly the four frozen pathways

The filter must match stable IDs in GMT column 2. Do not select pathways by a
case-insensitive search for the word `mitochondrial`.

```bash
Rscript - <<'RS'
source_path <- file.path(
  "data", "reference", "mitochondrial_extended",
  "ReactomePathways.v97.gmt")
output_path <- file.path(
  "data", "reference", "mitochondrial_extended",
  "mitochondrial_extended_gene_sets.gmt")
partial_path <- paste0(output_path, ".part")

pathway_ids <- c(
  "R-HSA-1592230",
  "R-HSA-5205647",
  "R-HSA-9840373",
  "R-HSA-9841251"
)
expected_names <- c(
  "Mitochondrial biogenesis",
  "Mitophagy",
  "Cellular response to mitochondrial stress",
  "Mitochondrial unfolded protein response (UPRmt)"
)
expected_counts <- c(95L, 39L, 9L, 18L)

lines <- readLines(source_path, warn = TRUE)
fields <- strsplit(lines, "\t", fixed = TRUE)
stopifnot(all(lengths(fields) >= 3L))

source_ids <- vapply(fields, function(x) x[[2]], character(1))
matches_per_id <- vapply(
  pathway_ids,
  function(id) sum(source_ids == id),
  integer(1))
stopifnot(all(matches_per_id == 1L))

selected <- fields[match(pathway_ids, source_ids)]
selected_names <- vapply(selected, function(x) x[[1]], character(1))
selected_counts <- vapply(
  selected,
  function(x) length(unique(x[-c(1, 2)])),
  integer(1))
union_count <- length(unique(unlist(
  lapply(selected, function(x) x[-c(1, 2)]),
  use.names = FALSE)))

stopifnot(
  identical(selected_names, expected_names),
  identical(selected_counts, expected_counts),
  union_count == 157L)

writeLines(
  vapply(selected, paste, collapse = "\t", character(1)),
  partial_path,
  useBytes = TRUE)
stopifnot(file.rename(partial_path, output_path))
RS

printf '%s  %s\n' \
  'f4d8b6c7a74894929028805e5e3cf81523968f8eecc380ac52b47038c5f9b847' \
  'data/reference/mitochondrial_extended/mitochondrial_extended_gene_sets.gmt' | \
  sha256sum --check --strict
```

### Step 5: create the provenance manifest

The manifest must have one row per selected pathway and record at least:

- schema version;
- resource name and Reactome version;
- release identifier/month, download date, and immutable source URL;
- source and derived paths;
- source ZIP, extracted GMT, and derived GMT SHA-256 values;
- Reactome stable ID and pathway name;
- Reactome review status;
- source gene count;
- HGNC-normalized MitoCarta overlap and extended-only count;
- selection rule and tier-precedence rule;
- Reactome data license;
- HGNC and MitoCarta paths and hashes;
- validation status.

Recommended frozen values:

```text
schema_version: mitochondrial_extended_manifest_v1
resource: Reactome
resource_version: 97
resource_release_month: 2026-06
download_date: 2026-07-18
source_url: https://reactome.org/download/97/ReactomePathways.gmt.zip
license: CC0-1.0
selection_rule: exact stable-ID match to four predeclared human pathways
tier_rule: MitoCarta and mtDNA-noncoding precedence before mito_extended
validation_status: validated_complete
```

Generate the manifest from the validated GMT, HGNC, and MitoCarta inputs.
Do not hand-enter gene membership or infer overlap by unnormalized symbols.

## Local validation

After the manifest has been generated:

```bash
test -r data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.zip
test -r data/reference/mitochondrial_extended/ReactomePathways.v97.gmt
test -r data/reference/mitochondrial_extended/mitochondrial_extended_gene_sets.gmt
test -r data/reference/mitochondrial_extended/mitochondrial_extended_manifest.tsv

printf '%s  %s\n' \
  '8c1dbc8578431da5d2d5118262718c60b553a9be3398e93658daa069e4a9afd4' \
  'data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.zip' | \
  sha256sum --check --strict

printf '%s  %s\n' \
  '89983d5c1f0af11c52edfeee7323eb425580ac6281d387a528562ab1787ce56b' \
  'data/reference/mitochondrial_extended/ReactomePathways.v97.gmt' | \
  sha256sum --check --strict

printf '%s  %s\n' \
  'f4d8b6c7a74894929028805e5e3cf81523968f8eecc380ac52b47038c5f9b847' \
  'data/reference/mitochondrial_extended/mitochondrial_extended_gene_sets.gmt' | \
  sha256sum --check --strict

printf '%s  %s\n' \
  '8d77d6782872d6d19eb98a6297c92dda686dfba719199c6c0b6346d4127fb4ec' \
  'data/reference/mitochondrial_extended/mitochondrial_extended_manifest.tsv' | \
  sha256sum --check --strict

Rscript - <<'RS'
path <- file.path(
  "data", "reference", "mitochondrial_extended",
  "mitochondrial_extended_gene_sets.gmt")
fields <- strsplit(readLines(path), "\t", fixed = TRUE)
ids <- vapply(fields, function(x) x[[2]], character(1))
counts <- vapply(
  fields,
  function(x) length(unique(x[-c(1, 2)])),
  integer(1))
genes <- unique(unlist(
  lapply(fields, function(x) x[-c(1, 2)]),
  use.names = FALSE))

stopifnot(
  length(fields) == 4L,
  identical(
    ids,
    c(
      "R-HSA-1592230",
      "R-HSA-5205647",
      "R-HSA-9840373",
      "R-HSA-9841251")),
  identical(counts, c(95L, 39L, 9L, 18L)),
  length(genes) == 157L)
cat("Extended Reactome reference validated\n")
RS
```

The HGNC-normalized validation must additionally confirm:

- 77 union genes are MitoCarta core;
- 80 union genes are extended-only;
- all 80 extended-only genes are present in the local Vasculature feature
  universe;
- 77 of the 80 are locally test-eligible;
- the three present but ineligible genes are exactly `DEFA5`, `PRKAG3`,
  and `UBE2V1`.

## Phase 09 configuration and code changes

After the reference bundle validates, add these values to
`config/phase09_annotation.yml`:

```yaml
extended_tier:
  enabled: true
  source: Reactome
  version: 97
  gene_sets_path: data/reference/mitochondrial_extended/mitochondrial_extended_gene_sets.gmt
  manifest_path: data/reference/mitochondrial_extended/mitochondrial_extended_manifest.tsv
  source_zip_path: data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.zip
  source_gmt_path: data/reference/mitochondrial_extended/ReactomePathways.v97.gmt
  source_zip_sha256: 8c1dbc8578431da5d2d5118262718c60b553a9be3398e93658daa069e4a9afd4
  source_gmt_sha256: 89983d5c1f0af11c52edfeee7323eb425580ac6281d387a528562ab1787ce56b
  gene_sets_sha256: f4d8b6c7a74894929028805e5e3cf81523968f8eecc380ac52b47038c5f9b847
  pathway_ids:
    - R-HSA-1592230
    - R-HSA-5205647
    - R-HSA-9840373
    - R-HSA-9841251
```

The implementation must:

1. verify all configured reference hashes before reading gene membership;
2. require exactly the four stable IDs and their expected counts;
3. normalize symbols through the frozen HGNC reference;
4. apply MitoCarta and mtDNA-noncoding precedence;
5. retain one-to-many Reactome pathway membership in long format;
6. label only the 80 non-core union members as `mito_extended`;
7. record UPRmt review status 3/5 in provenance;
8. fail rather than silently disabling the tier when
   `extended_tier.enabled: true` and an input is absent or mismatched.

Do not modify `config/analysis_parameters.yml`, because Phase 08 records its
checksum.

## Acceptance criteria

The extended reference is ready when:

- the immutable Reactome V97 ZIP matches its frozen SHA-256;
- the extracted full GMT matches its frozen SHA-256;
- the derived GMT matches its frozen SHA-256;
- the derived GMT has exactly four rows and the four prespecified stable IDs;
- individual source counts are 95, 39, 9, and 18;
- the union contains 157 source symbols;
- HGNC normalization yields 77 core and 80 extended-only genes;
- all mapping ambiguities are reported rather than resolved by row order;
- the manifest records source, version, URL, license, review status, hashes,
  and selection rules;
- Phase 09 config enables the tier only after all checks pass.

## Implementation checklist

### Acquire and freeze

- [x] Create `data/reference/mitochondrial_extended/`.
- [x] Download the immutable Reactome V97 ZIP.
- [x] Validate the ZIP checksum before publishing it.
- [x] Extract and validate the complete V97 GMT.
- [x] Select the four pathways by exact stable ID.
- [x] Validate individual and union gene counts.
- [x] Generate and validate the provenance manifest.

### Integrate

- [x] Normalize Reactome and MitoCarta symbols through frozen HGNC.
- [x] Validate the expected 77-core/80-extended split.
- [ ] Add the frozen paths, hashes, and IDs to
  `config/phase09_annotation.yml`.
- [ ] Implement reference validation and tier precedence in Phase 09.
- [ ] Keep complete pathway membership while assigning only non-core genes to
  `mito_extended`.

### Finalize locally

- [x] Validate all four local reference files.
- [x] Confirm all four artifact checksums, including the generated manifest.
- [x] Update the main Phase 09 plan checklist.
- [ ] Run Phase 09 only after the local extended-reference preflight passes.

## Authoritative references

- [Reactome V97 release announcement](https://reactome.org/about/news/295-v97-released)
- [Reactome download documentation](https://reactome.org/download-data/)
- [Reactome data license](https://reactome.org/license)
- [Reactome review-status definitions](https://www.reactome.org/userguide/review-status)
- [Reactome mitochondrial biogenesis, R-HSA-1592230](https://reactome.org/content/detail/R-HSA-1592230)
- [Reactome mitophagy, R-HSA-5205647](https://reactome.org/content/detail/R-HSA-5205647)
- [Reactome cellular response to mitochondrial stress, R-HSA-9840373](https://reactome.org/content/detail/R-HSA-9840373)
- [Reactome mitochondrial unfolded protein response, R-HSA-9841251](https://reactome.org/content/detail/R-HSA-9841251)
- [Gene Ontology annotation downloads and archives](https://geneontology.org/docs/download-go-annotations/)
- [Gene Ontology citation and licensing policy](https://geneontology.org/docs/go-citation-policy/)
- [MSigDB Reactome mitochondrial biogenesis set](https://www.gsea-msigdb.org/gsea/msigdb/human/geneset/REACTOME_MITOCHONDRIAL_BIOGENESIS.html)
- [MitoMiner/IMPI description](https://www.mrc-mbu.cam.ac.uk/research-resources-and-facilities/mitominer)

