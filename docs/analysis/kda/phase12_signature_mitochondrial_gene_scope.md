# Are All Phase 12 Signature Genes Mitochondrial?

By design, every gene passed in a Phase 12 signature is labeled as
mitochondrial. However, there are two important qualifications:

1. the signature is only a subset of the mitochondrial genes; and
2. the mitochondrial annotation may include mapping errors that require
   auditing.

## How the signature is selected

The effective signature for a Phase 12 run is:

```text
Phase 08 paper DEG
∩ core_mito_protein
∩ requested expression direction
∩ genes present in the induced network
```

This is implemented in
[`scripts/12_run_kda.R`](../../../scripts/12_run_kda.R):

```r
deg <- source_rows[
  paper_deg == TRUE &
  mito_tier %in% tiers
]
```

The Phase 12 configuration sets:

```yaml
query_universe:
  profile: core_mito
  mito_tiers: [core_mito_protein]
```

See [`config/phase12_kda.yml`](../../../config/phase12_kda.yml).

Phase 12 then separates those genes by expression direction:

```r
up <- sort(unique(deg[logFC > 0, mapped_gene]))
down <- sort(unique(deg[logFC < 0, mapped_gene]))
```

The direction-specific candidate sets are:

```r
candidate_sets <- list(
  AD_up_mito = up,
  AD_down_mito = down,
  AD_both_mito = sort(unique(c(up, down)))
)
```

Finally, Phase 12 retains only candidate genes that occur in the induced
network:

```r
effective <- intersect(candidate, background)
sig <- data.frame(
  Var = effective,
  Group = run_id,
  stringsAsFactors = FALSE
)
```

Only `effective`, rather than the complete candidate set, is passed to
`call_key_drivers()`.

## The signature does not contain all mitochondrial genes

A signature contains only mitochondrial genes that are significant
differentially expressed genes for the particular:

- cell type;
- sex/APOE group or pooled group;
- AD-versus-NCI contrast; and
- expression direction.

The three signature directions mean:

- `AD_up_mito`: only upregulated mitochondrial DEGs;
- `AD_down_mito`: only downregulated mitochondrial DEGs; and
- `AD_both_mito`: the union of the upregulated and downregulated
  mitochondrial DEGs.

A mitochondrial gene is not included in the effective signature if it:

- does not satisfy the Phase 08 `paper_deg` rule;
- has the wrong expression direction for the run; or
- is absent from the induced network.

In `kda_signature_members.tsv.gz`, `effective_member = TRUE` identifies the
genes that were actually passed to `call_key_drivers()`. Rows with
`effective_member = FALSE` were direction-specific candidates but were not
passed because they were outside the effective network background.

## “Mitochondrial” does not mean only `MT-*` genes

For Phase 12, `core_mito_protein` means genes classified as canonical Human
MitoCarta3.0 protein members by Phase 09.

This category contains many nuclear-encoded mitochondrial proteins. Therefore,
most signature genes are not necessarily located on mitochondrial DNA and do
not necessarily have names beginning with `MT-`.

Phase 12 excludes the other Phase 09 tiers:

| Tier | Phase 12 status |
|---|---|
| `core_mito_protein` | Included |
| `mtdna_noncoding` | Excluded |
| `mito_extended` | Excluded |
| `non_mito` | Excluded |

`mtdna_noncoding` includes mitochondrial rRNA and tRNA genes.
`mito_extended` contains the extended pathway-based mitochondrial-related
genes rather than canonical MitoCarta protein members.

## Important annotation concern: `RPL13` versus `MRPL13`

Although every signature gene is labeled `core_mito_protein` by the pipeline,
that annotation may not be perfectly clean.

For example, `RPL13` appears as an effective Phase 12 signature gene. The
Phase 09 annotation records:

```text
symbol_hgnc_current:          RPL13
mitocarta_canonical_symbol:   MRPL13
phase03_mitocarta_match_type: unique_synonym
mito_tier:                    core_mito_protein
```

Thus, the measured and HGNC-resolved gene remains `RPL13`, but its
mitochondrial classification came from a synonym match to the different gene
`MRPL13`.

This is a potential cross-gene alias-mapping false positive. `RPL13` and
`MRPL13` should not be treated as the same gene merely because one reference
lists a symbol as an alias.

## Interpretation

The precise conclusion is:

> All genes passed in Phase 12 signatures are labeled `core_mito_protein` by
> Phase 09, but they are not necessarily all unquestionably mitochondrial
> genes biologically.

The intended input is a direction-specific set of significant, canonical
MitoCarta mitochondrial-protein DEGs that are present in the effective
network. The observed `RPL13 -> MRPL13` mapping indicates that Phase 09's
MitoCarta matching should be audited for cross-gene alias collisions before
every signature member is treated as a validated mitochondrial gene.
