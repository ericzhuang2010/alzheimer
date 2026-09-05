# SEA-AD genotype-source decision: NG00174 WGS versus the available SNP array

## Why the original plan requested NG00174 WGS

`NG00174` is a NIAGADS dataset accession, not a file format. It identifies a
SEA-AD genetics release containing, among other products, whole-genome
sequencing (WGS) genotypes for 84 samples. The input requested by the
original plan was the joint, chromosome-level GRCh38 VCF callset. See the
[NIAGADS NG00174.v1 dataset page](https://dss.niagads.org/datasets/ng00174/).

The intended role of these data is:

```text
Matched donor genotypes + donor gene expression
                  |
                  v
              cis-eQTLs
                  |
                  v
        genetic instruments for CIT
                  |
                  v
     directional priors for RIMBANet
                  |
                  v
        seven gene-regulatory networks
```

For each donor, the workflow needs both gene-expression measurements from the
SEA-AD pseudobulk data and genotypes showing which DNA variants that donor
carries. It then tests whether variants within 1 Mb of a gene are associated
with that gene's expression. These associations are cis-eQTLs. Significant
variants can serve as genetic instruments in the CIT analysis, helping assess
which direction between two associated genes is better supported.

Genetic variants are not network nodes. They provide evidence used to
orient gene-to-gene edges. Expression association alone generally cannot
distinguish `Gene A -> Gene B` from `Gene B -> Gene A`.

The integrative method requires:

- At least 50 donors explicitly matched between genotype and expression data.
- Genotype QC and ancestry covariates.
- cis-eQTL discovery.
- CIT-derived directional evidence.
- RIMBANet priors built from CIT and ENCODE evidence.

The pre-refactor configuration makes genetics mandatory but still contains
the superseded NG00174 dataset label:

```yaml
method:
  mode: full_integrative
  allow_expression_only_fallback: false

genetics:
  required: true
  dataset: NIAGADS_NG00174
  minimum_matched_donors: 50
```

The locally available array contains the genotypes needed for a modified
eQTL analysis. It has less comprehensive variant coverage than WGS, so using
it requires an explicit change to the input contract, provenance, genotype
preparation, and statistical expectations.

In short, NG00174 WGS was specified because the accepted plan promises
genetically informed, directionally constrained networks. It is not inherently
the only genotype source that could support the method.

## Decision on using the available SNP-array VCF

Decision: adopt the `syn49430589` SNP-array VCF as the primary genotype
source for this build. The donor-identity suitability gate passed. The method
fundamentally needs matched germline genotypes; it does not inherently require
that those genotypes were measured by WGS.

This is a reasonable option because:

- The available array is the Illumina Global Diversity Array-8, a high-density
  array with approximately 1.8 million markers and design support for
  cross-population imputation. See the
  [Illumina GDA-8 specifications](https://www.illumina.com/products/by-type/microarray-kits/infinium-global-diversity.html).
- The current analysis excludes rare variants with `MAF < 5%`, so it would not
  use much of WGS's rare-variant advantage.
- With approximately 78 expression donors, sample size will probably limit
  eQTL discovery more strongly than the distinction between a high-density
  array and WGS.
- The professor specifically directed the search to the shared SEA-AD
  directory containing this array dataset, which suggests it may have been the
  intended genotype source.

The disadvantages and risks are:

- Array genotyping measures selected sites, while WGS observes variants much
  more comprehensively.
- Without imputation, some genes may have inadequate nearby variants, yielding
  fewer cis-eQTL instruments and fewer CIT-directed edges.
- Imputation quality varies with ancestry, reference panel, and genomic region;
  array data are not uniformly equivalent to WGS. See this
  [array-imputation versus WGS study](https://pubmed.ncbi.nlm.nih.gov/35981533/).
- Header and identity audits established VCFv4.2, 95 hard-called `GT`
  samples, a GRCh37 D1 manifest, and exact one-to-one suffix matches for all 78
  primary expression donors. GRCh38 marker mapping, allele representation, and
  genotype quality still require validation.
- The final network must be described as using **SNP-array-derived genetic
  priors**, not WGS-derived priors.

The operational decision rule is:

> Use the SNP-array VCF if it contains at least 50 authoritatively matched
> expression donors, has a known or validly convertible genome build, and
> passes genotype QC. Retain the prespecified statistical thresholds and
> explicitly report sparse eQTL/CIT coverage. Do not claim equivalence to WGS.

The identity gate passed and the build plan now adopts the GDA-8 array. The
source archive is frozen at SHA-256
`f9d60b00db44e6a4f7c96329b1b8bbc1998dc96b3f4b1c4d3d4d274812dc9459`.
The official D2/GRCh38 manifest ZIP is frozen at SHA-256
`bba55d6b646491fc2794e6b56b524200d82db8e4ed0d5ca55b02a57c36073d7a`. The
full identifier audit established `Name` as the exact join field: all 992,665
eligible unique source IDs matched it, with zero source or D2-name duplicates;
991,538 matches had a valid GRCh38 target. All 1,127 invalid D2 targets are
unplaced. The rejected source records comprise 107 unplaced records, 9,933
additional missing-reference records, and 901,894 additional missing-alternate
records. The 991,538 exact, unique, placed candidates advance to reference-
allele and strand validation. The
configuration and executable VH11 scripts still require the corresponding
generic-genotype refactor before production resumes. The array VCF, explicit
crosswalk, and all derived participant-level genotype data must remain outside
Git.

### Read-only VCF header audit on Minerva

Run:

```bash
GENO_ROOT=/sc/arion/projects/adineto/sea_ad/Data/SNP_Genomic_Variants
ARCHIVE="$GENO_ROOT/SEA_AD_SNPs_vcf.tar.gz"

tar -xOzf "$ARCHIVE" SEA_AD_SNPs_vcf/sea_ad.vcf 2>/dev/null |
awk -F '\t' '
/^##fileformat=/ {
    print
}
/^##reference=/ {
    print
}
/^##contig=<ID=(chr)?1,/ {
    print "chromosome_1_definition=" $0
}
/^#CHROM/ {
    print "sample_count=" NF - 9
    next
}
!/^#/ {
    print "first_variant=" $1 ":" $2 ":" $4 ":" $5
    print "format_field=" $9
    exit
}'
```

This reports only structural metadata and the sample count; it does not print
participant identifiers or extract the VCF to disk.

Observed result:

```text
fileformat: VCFv4.2
samples: 95
genotype field: GT
source manifest: GDA-8v1-0_d1 (GRCh37)
first record: 0:0:N:. (unmapped placeholder requiring exclusion)
```

A subsequent privacy-preserving identity audit produced:

```text
primary expression donors: 78
one-to-one suffix matches: 78
unmatched expression donors: 0
ambiguous expression donors: 0
duplicate sample assignments: 0
VCF samples outside primary cohort: 17
VCF samples with numeric prefix: 95
PASSED: strict one-to-one genotype-to-expression identity gate
```

The frozen mapping rule is an exact numeric prefix, underscore, and donor ID:
`^[0-9]+_(<donor_id>)$`. Row-order matching is prohibited.
