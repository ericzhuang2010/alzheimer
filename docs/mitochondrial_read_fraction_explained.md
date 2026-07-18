# Mitochondrial Read Fraction (`percent.mt`)

**Mitochondrial read fraction**, often labeled **`percent.mt`**, is a per-nucleus quality-control measurement in single-nucleus RNA sequencing.

For each nucleus, the analysis asks:

> Of all RNA molecules detected in this nucleus, what percentage came from genes encoded by the mitochondrial genome?

The RNA molecules are counted using **UMIs**—unique molecular identifiers that help estimate how many original RNA molecules were captured.

For example, suppose a nucleus has:

- 2,000 total UMIs
- 100 UMIs assigned to mitochondrial genes

Then:

\[
\text{percent.mt} = \frac{100}{2000} \times 100 = 5\%
\]

## What a high mitochondrial fraction can mean

A higher `percent.mt` may have several possible explanations:

**Poor RNA or nucleus quality.** When a cell is damaged or dying, nuclear and cytoplasmic RNA may be lost or degraded unevenly, making mitochondrial RNA appear disproportionately abundant.

**Cellular stress.** Stressed cells can genuinely alter mitochondrial transcription or retain more mitochondrial RNA.

**Real mitochondrial biology.** Some cell types naturally have greater mitochondrial activity because of their energy demands.

**Technical effects.** In single-nucleus data, mitochondrial RNA may also reflect incomplete nucleus isolation, attached cytoplasmic material, or ambient RNA contamination.

## Why it should be interpreted separately from pathway expression

`percent.mt` is a **proportion of all detected RNA**, not a direct measurement of whether a mitochondrial biological pathway is active.

A high percentage could occur because:

- mitochondrial RNA increased;
- non-mitochondrial RNA decreased;
- the nucleus was damaged;
- or several of these happened together.

By contrast, a pathway-expression score examines the expression pattern of a defined set of genes involved in a process such as oxidative phosphorylation, mitochondrial translation, or the stress response. Many of those pathway genes are encoded in the **nuclear genome**, not the mitochondrial genome.

So the main point is:

> **`percent.mt` is primarily a composition and quality metric, whereas mitochondrial pathway expression is a gene-program activity metric. They may be related, but they are not interchangeable.**