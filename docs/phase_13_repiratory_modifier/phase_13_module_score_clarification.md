# Phase 13 module-score clarification

## Terminology: module and program mean the same thing

In Phase 13, **gene module** and **gene program** mean the same thing: a
prespecified group of genes that perform a related biological function.

- **Module** is the technical term used in code, configuration, statistical
  models, and output filenames.
- **Program** is the plain-language biological term used in explanations and
  result summaries.
- **Module score** or **program score** is the numerical summary calculated for
  one donor, one module/program, and one broad cell context.

For example:

| Technical name | Equivalent biological wording |
|---|---|
| mtDNA OXPHOS module | mtDNA OXPHOS program |
| Nuclear OXPHOS module | Nuclear OXPHOS program |
| Mitochondrial-translation module | Mitochondrial-translation program |
| MIB/MICOS module | Inner-membrane-organization program |

Throughout this document, **module/program** refers to the gene set itself,
whereas **module/program score** refers to the donor-level numerical summary of
that gene set.

## All-gene normalization versus module/program scoring

Phase 13 normalizes all genes, but it does **not** calculate one score using
all genes. Each module/program score uses only the admitted genes belonging to
that frozen module/program.

```text
All-gene raw counts
        |
        v
All-gene filtering and TMM/logCPM normalization
        |
        +-- Gene-level models: all adequately measured genes
        |
        +-- camera background: all adequately measured genes
        |
        `-- Module/program scores: only genes in each frozen module/program
```

The four module/program scores are calculated from:

- **mtDNA OXPHOS score:** admitted genes from the frozen 13-gene list only;
- **nuclear OXPHOS score:** admitted genes from the frozen 86-gene list only;
- **mitochondrial-translation score:** admitted genes from the frozen 155-gene
  list only; and
- **MIB/MICOS score:** admitted genes from the frozen 19-gene list only.

A module/program gene is admitted when it:

1. maps uniquely to the assay;
2. passes the all-transcriptome expression filter; and
3. has a finite, nonzero NCI standard deviation.

For donor `d`, module `m`, and broad cell context `c`, first standardize every
admitted module gene `g` using eligible NCI donors from the same context:

```text
z(d,g,c) =
    [logCPM(d,g,c) - mean_NCI(g,c)]
    / sd_NCI(g,c)
```

Then calculate the module score using only the admitted genes in module `m`:

```text
raw_mean_z(d,m,c) =
    mean of z(d,g,c) over admitted genes g in module m
```

The primary outcome is this donor score standardized once more using its NCI
donor distribution:

```text
standardized_score(d,m,c) =
    [raw_mean_z(d,m,c) - module_mean_NCI(m,c)]
    / module_sd_NCI(m,c)
```

One unit of `standardized_score` is one NCI donor-level module-score standard
deviation in that broad cell context.

The precise rule is:

> Normalize the complete usable transcriptome, but calculate each module score
> using only the eligible genes from that prespecified module.

All-gene normalization is needed for valid library-depth and composition
adjustment and for the full-transcriptome `camera` background. It does not mean
that non-module genes enter a module score. Significant-DEG status, P values,
q values, and observed fold changes are not used to select or weight genes in
the primary module score.

See the main plan sections on [all-gene normalization](phase_13_respiratory_modifier_plan.md#all-gene-normalization), [module coverage](phase_13_respiratory_modifier_plan.md#module-coverage), and the [primary donor module score](phase_13_respiratory_modifier_plan.md#primary-donor-module-score).
