# Using call_key_drivers for key-driver analysis

This note summarizes how to use `call_key_drivers()` from the NetWeaver-style helper in this project.

## What the function does

`call_key_drivers()` tests whether certain upstream network nodes have downstream neighborhoods that are significantly enriched for a given gene signature. In practice, it is used to identify candidate key drivers of a biological response represented by DEGs or other gene sets.

## Inputs

### 1. Network input

The first input is a network as a two-column data frame:

- first column: source node
- second column: target node

Example:

```r
net <- data.frame(
  from = c("A", "B", "C"),
  to   = c("B", "C", "D")
)
```

This represents directed edges:

- A -> B
- B -> C
- C -> D

### 2. Signature input

The second input is a data frame with at least two columns:

- `Var`: gene names / signature genes
- `Group`: signature label or group name

Example:

```r
signatures <- data.frame(
  Var = c("C", "D", "A", "B"),
  Group = rep(c("Male_vs_Female", "Apoe4_vs_Apoe3"), each = 2)
)
```

This means:

- `C` and `D` belong to `Male_vs_Female`
- `A` and `B` belong to `Apoe4_vs_Apoe3`

### Optional arguments

The function also accepts optional arguments such as:

- `nLayerToTest`: how far downstream to test
- `nLayersToExpand`: how much to expand the signature
- `bg.size`: background size for the enrichment test
- `directed`: whether the network is directed
- `reduce.within.nlayer`: how aggressively to collapse nearby candidates
- `fdr`: false discovery rate threshold
- `p.correction.method`: multiple-testing correction method
- `return.overlap`: whether to return overlapping genes in the result

## Output

`call_key_drivers()` returns a data frame of predicted key-driver results.

Each row corresponds to a candidate key driver for one signature group. Typical output columns include:

- `Signature`: the group label
- `Keydriver`: the candidate driver gene
- `BestLayer`: the best layer at which the enrichment was detected
- `q`: number of overlapping query genes in the neighborhood
- `m`: size of the neighborhood tested
- `n`: background size remaining after subtraction
- `k`: size of the query signature
- `FE`: fold enrichment
- `log.P.Value`: enrichment statistic on log scale
- `adj.P.Value`: adjusted P value
- `global.Keydriver`: whether the candidate is considered a global key driver

If no significant result is found, the function may return `NULL` or an empty-style result depending on the input.

## Minimal example

```r
source("scripts/NetWeaver/fKDA.R")

net <- data.frame(
  from = c("A", "B", "C"),
  to   = c("B", "C", "D")
)

signatures <- data.frame(
  Var = c("C", "D", "A", "B"),
  Group = rep(c("Male_vs_Female", "Apoe4_vs_Apoe3"), each = 2)
)

res <- call_key_drivers(net, signatures)
res
```

## Example with a custom background size

If you want to use a more realistic background for your analysis, you can provide `bg.size`:

```r
res2 <- call_key_drivers(
  net = net,
  signature.df = signatures,
  bg.size = 1000,
  directed = TRUE,
  fdr = 0.05
)
```

## How this maps to your project

For the Alzheimer project, the likely use is:

- `net`: one cell-type Bayesian network
- `signature.df`: mitochondrial DEGs grouped by contrast or stratum
- `bg.size`: the number of genes tested in the matching contrast and present in the network

A typical structure would be:

```r
signatures <- data.frame(
  Var = mito_degs,
  Group = contrast_label
)

res <- call_key_drivers(
  net = bn_net,
  signature.df = signatures,
  bg.size = bg_size,
  directed = TRUE,
  fdr = 0.05
)
```

## Practical notes

- The `Group` column is only a label for each signature set.
- The function will run the analysis separately for each unique `Group` value.
- The names in `Var` should match the node names in the network as closely as possible.
- For real analyses, use the network and DEG sets that match the same cell type and contrast.

## Summary

The core idea is simple:

1. provide a directed network,
2. provide one or more gene signature groups,
3. run `call_key_drivers()`, and
4. inspect the resulting table of candidate key drivers.
