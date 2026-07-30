# How Phase 12 Finds Key Drivers and Selects the Best Layer

## Overview

For each Phase 12 `run_id`, the key-driver analysis receives:

- a directed Bayesian network, represented as `source_gene -> target_gene`;
- a signature containing the genes associated with that `run_id`; and
- a background containing the genes eligible for the enrichment test.

The key-driver implementation is in
[`scripts/NetWeaver/fKDA.R`](../../../scripts/NetWeaver/fKDA.R), and Phase 12
calls it from [`scripts/12_run_kda.R`](../../../scripts/12_run_kda.R) with a
maximum of three network layers.

The analysis has three main stages:

1. find genes that could be candidate drivers;
2. build the directed downstream neighborhood of each candidate; and
3. test whether each neighborhood is enriched for the signature.

## 1. Finding candidate drivers

Starting from the signature genes, the code searches the network up to three
edges away. Edge direction is ignored during this initial candidate search.

Any gene within three undirected network steps of a signature gene can become
a candidate driver.

Direction is ignored at this stage because a real upstream candidate might
look like:

```text
candidate driver -> intermediate gene -> signature gene
```

If the search started at the signature and only followed edge direction, it
would move downstream and would not find that upstream candidate.

This first search only limits the genes that must be tested. Being found during
the candidate search does not make a gene a key driver.

## 2. Constructing directed downstream neighborhoods

For every candidate, the code follows directed outgoing edges and constructs
cumulative neighborhoods for layers 1, 2, and 3.

For example:

```text
D -> A -> B -> C
 \
  -> E
```

The neighborhoods of candidate `D` are:

| Layer | Cumulative neighborhood |
|---|---|
| 1 | `D, A, E` |
| 2 | `D, A, E, B` |
| 3 | `D, A, E, B, C` |

A layer is therefore a network radius:

- Layer 1 contains the candidate and genes reachable within one directed edge.
- Layer 2 contains the candidate and genes reachable within at most two
  directed edges.
- Layer 3 contains the candidate and genes reachable within at most three
  directed edges.

The layers are cumulative. Layer 2 does not mean only the genes that are
exactly two edges away.

The candidate itself is included in its cumulative neighborhood. Consequently,
if the candidate is also a signature gene, it may contribute to the signature
overlap. The `is_signature` column records whether this is the case.

## 3. Testing signature enrichment at every layer

For every candidate and every available layer, the code calculates:

- `q`: number of signature genes in the cumulative neighborhood;
- `m`: number of background genes in that neighborhood;
- `k`: total signature size; and
- `M`: total background size.

It then applies an upper-tail hypergeometric test:

$$
P = P(X \ge q).
$$

The statistical question is:

> If `m` genes were selected from a background of `M` genes, how surprising
> would it be to observe at least `q` members of a signature containing `k`
> genes?

A small P value means that the candidate's downstream neighborhood contains
more signature genes than expected by chance.

The fold enrichment is:

$$
\mathrm{FE}
= \frac{q/m}{k/M}
= \frac{qM}{mk}.
$$

For example, `FE = 5` means that signature genes occur five times more
frequently in the candidate's neighborhood than in the overall background.

## What `best_layer` means

The code evaluates each candidate at layers 1, 2, and 3, sorts those results by
the unadjusted hypergeometric P value, and retains the layer with the smallest
P value.

Therefore:

> `best_layer` is the cumulative network radius at which that candidate showed
> the strongest statistical enrichment for the signature.

In particular:

- `best_layer = 1` means the neighborhood within one directed edge produced
  the smallest P value.
- `best_layer = 2` means the neighborhood within at most two directed edges
  produced the smallest P value.
- `best_layer = 3` means the neighborhood within at most three directed edges
  produced the smallest P value.

`best_layer` does **not** mean:

- that the driver is exactly two or three edges away from every signature gene;
- that the selected radius is the true biological distance;
- that the deepest layer is biologically best; or
- that the selected layer necessarily has the largest overlap or the highest
  fold enrichment.

The selected layer is based specifically on the smallest raw hypergeometric P
value.

## Why the largest layer is not always best

Increasing the layer can add signature genes, but it can also add many
non-signature genes.

For example:

| Layer | Neighborhood size | Signature overlap |
|---|---:|---:|
| 1 | 5 | 2 |
| 2 | 15 | 4 |
| 3 | 100 | 5 |

Although layer 3 contains the largest number of signature genes, it also
contains many additional background genes. Its enrichment may therefore be
weaker than the enrichment at layer 2.

The hypergeometric test balances:

- how many signature genes were captured; and
- how large the entire neighborhood became.

This allows a compact, concentrated layer to outperform a larger, more diluted
layer.

## Phase 12 example: `RPL13`

For the run `primary_Ast_CHI3L1_F_e2_AD_up_mito`, the result for `RPL13`
includes approximately:

| Field | Value |
|---|---:|
| Background size | 6,943 |
| Signature size | 6 |
| `best_layer` | 2 |
| Neighborhood size | 18 |
| Signature overlap | 2 |
| Fold enrichment | 128.57 |
| Adjusted P value | 0.01268 |
| Overlap genes | `RPL13;FKBP8` |

This result means:

1. The code evaluated the directed neighborhoods of `RPL13` at radii 1, 2,
   and 3.
2. The cumulative radius-2 neighborhood contained 18 background genes.
3. Two of the six signature genes, `RPL13` and `FKBP8`, were in that
   neighborhood.
4. Radius 2 produced the smallest raw hypergeometric P value among the tested
   radii.
5. The result remained significant after Benjamini-Hochberg adjustment.

Thus, `RPL13` was reported as a key driver with `best_layer = 2`.

Because `RPL13` is itself a signature gene, it contributes one of the two
overlapping genes. That should be considered when interpreting this result.

## How a candidate becomes a reported key driver

After choosing one best layer per candidate, the code:

1. converts the stored log P value back to a regular P value;
2. applies Benjamini-Hochberg correction across the candidates for that run;
   and
3. retains candidates with an adjusted P value no greater than `0.05`.

Each retained candidate becomes one row in `kda_results.tsv.gz`. A single
`run_id` can therefore have multiple key drivers.

Candidates that do not pass the adjusted-P-value threshold are not written to
the final results.

## What `global_key_driver` means

After identifying significant drivers, the code compares them with one another
using a two-layer directed neighborhood.

A significant driver is marked as global when it is not located within two
downstream layers of another significant driver from the same run.

Conceptually:

```text
Driver A -> intermediate -> Driver B -> signature genes
```

In this situation:

- `Driver A` may be marked global.
- `Driver B` may still be a significant key driver, but it is more downstream
  and may be marked non-global.

`global_key_driver = TRUE` means that the driver is a more upstream
representative among the significant drivers for that run. It does not mean
that the gene is globally important in every cell type, contrast, signature,
or network.

Non-global drivers are not removed; they remain in `kda_results.tsv.gz`.

## Interpretation and limitations

A reported key driver means:

> The gene's directed downstream network neighborhood is statistically
> enriched for the Phase 12 signature.

It does not by itself prove that:

- the gene causally drives Alzheimer's disease;
- the network edge direction is experimentally confirmed;
- the selected layer is a real physical or temporal biological distance; or
- perturbing the driver will necessarily reverse the signature.

There is also an important implementation detail: the code chooses the
smallest raw P value across up to three layers and then performs
Benjamini-Hochberg correction on the selected candidate-level P values. It does
not apply a separate multiple-testing correction for searching several layers.
The reported significance should therefore be understood as the significance
definition implemented by this KDA algorithm.
