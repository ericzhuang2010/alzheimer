# fKDA zero-overlap hypergeometric boundary bug

## Resolution status

- **Status:** corrected, regression-tested, and frozen by checksum
- **Discovered:** 2026-07-27 during the Phase 12 local-pilot scientific
  invariant audit
- **Affected repository file:** `scripts/NetWeaver/fKDA.R`
- **Affected function:** `predictKeyDrivers()`, called by
  `call_key_drivers()`
- **Old, affected SHA-256:**
  `15d1708803310bd66720e089ffb02a30352c1d1ef556602ed867e1662b86efa0`
- **Corrected SHA-256:**
  `fed8f89f35a3f08f38a420eb9b26c590cdc5f13a12064af1b9fa4a4cb1168550`

This was a statistical boundary error in the copied NetWeaver-style KDA
implementation. It was not caused by the Phase 08 DEG calls, mitochondrial
gene filtering, fine-to-broad cell-type mapping, Bayesian-network direction,
or the Phase 12 background construction.

## Summary of the bug

For every candidate driver and tested network layer, `predictKeyDrivers()`
counts the overlap between the candidate's neighborhood and the query
signature. Let:

- `M` be the effective background size;
- `m` be the candidate neighborhood size;
- `M - m` be the number of background genes outside the neighborhood;
- `k` be the signature size; and
- `q` be the observed number of signature genes in the neighborhood.

The one-sided hypergeometric enrichment P value is:

```text
P(X >= q) = P(X > q - 1)
```

In R, the correct upper-tail calculation is therefore:

```r
phyper(q - 1, m, M - m, k, lower.tail = FALSE)
```

The affected code instead used:

```r
phyper(max(0, q - 1), m, M - m, k, lower.tail = FALSE)
```

For positive overlaps, `q >= 1`, both expressions are identical. The problem
occurs at the boundary `q = 0`:

```text
correct threshold: q - 1 = -1
affected threshold: max(0, q - 1) = 0
```

The correct P value for zero overlap is:

```text
P(X >= 0) = 1
```

The affected calculation instead evaluates:

```text
P(X > 0) = P(X >= 1)
```

That is the probability of observing at least one overlap, even though the
candidate actually had no overlap. When the expected number of overlaps is
small, this probability can itself be small. Consequently, a zero-overlap
candidate could pass the subsequent Benjamini-Hochberg FDR filter and be
reported as a significant key driver.

## Concrete Phase 12 example

One provisional local-pilot row for `MORF4L1` had:

```text
q = 0
m = 2
M - m = 3869
k = 3
FE = 0
```

The affected calculation produced:

```r
phyper(0, 2, 3869, 3, lower.tail = FALSE)
# 0.00154958656998
```

Its log P value was approximately `-6.469767`, even though its observed
overlap and fold enrichment were both zero. The corrected calculation is:

```r
phyper(-1, 2, 3869, 3, lower.tail = FALSE)
# 1
```

The combination `q = 0`, `FE = 0`, and a small adjusted P value was the key
diagnostic contradiction that led to the source-level audit.

## Impact on the first provisional pilot run

The first provisional run completed computationally and passed structural
checks, but it was scientifically invalid because the structural checks did
not yet require every reported driver to have positive query overlap.

| Metric | Provisional affected run | Corrected rerun |
|---|---:|---:|
| Planned KDA rows | 165 | 165 |
| Eligible KDA rows | 26 | 26 |
| Runs reported as significant | 26 | 23 |
| Eligible runs with no significant driver | 0 | 3 |
| Reported key-driver rows | 907 | 135 |
| Reported rows with `q = 0` | 680 | 0 |
| Failed KDA rows | 0 | 0 |

The 680 zero-overlap rows were not the only reason a complete rerun was
required. Their erroneous raw P values participated in the same
Benjamini-Hochberg adjustment as positive-overlap candidates. Therefore, it
would not be statistically valid to repair the provisional table merely by
deleting rows with `q = 0`; the raw P values and adjusted P values had to be
recomputed for every candidate.

The provisional bundle was removed from the results tree and moved intact to:

```text
/tmp/phase12_kda_provisional_zero_overlap_20260727
```

That temporary copy is retained only as a recoverable debugging artifact. It
must not be interpreted, copied into production, or used for biological
conclusions. The corrected pilot bundle is the nine-file output under:

```text
results/local_pilot/12_kda/
```

It is still labeled `nonfinal_smoke_test`; no Minerva production KDA was run
as part of this correction.

## Code correction

The corrected expression in `scripts/NetWeaver/fKDA.R` is:

```r
# q = 0 must have an upper-tail enrichment P value of 1.
phyper(q - 1, m, M - m, k, lower.tail = FALSE, log.p = TRUE)
```

In the actual function, the four values are supplied through the vector
created from the columns `q`, `m`, `n`, and `k`:

```r
phyper(x[1] - 1, x[2], x[3], x[4],
       lower.tail = FALSE, log.p = TRUE)
```

No other part of the KDA calculation was changed. Phase 12 continues to use
the requested `call_key_drivers()` entry point, directed networks, three
layers, BH correction, and the run-specific induced-network background.

The corrected source checksum is frozen in `config/phase12_kda.yml`. Phase 12
aborts before analysis if the on-disk source checksum differs from that
configuration.

## Added safeguards

Three layers of protection now prevent recurrence.

### 1. Deterministic regression test

`tests/test_phase12_kda.R` contains a directed positive-control network and a
direction-reversed control. In addition to checking directionality, it now
requires:

```r
all(result$q > 0)
```

The deterministic test passed after the correction.

### 2. Runtime fail-closed guard

After normalizing a `call_key_drivers()` result,
`scripts/12_run_kda.R` checks every reported row. If any significant row has
`overlap_count < 1`, the run is marked as `kda_error`, its result is rejected,
and the final Phase 12 validation cannot pass.

### 3. Final scientific-invariant audit

The corrected local bundle was validated to require all of the following:

- every reported `adjusted_p_value` is at most `0.05`;
- every reported `overlap_count` is positive;
- every overlap item is an effective member of that run's mitochondrial query;
- every reported key driver belongs to that run's effective background;
- all recorded artifact checksums match the published files;
- all three gzip outputs are readable; and
- all Phase 12 checks pass with zero failed runs.

The corrected local pilot contained 135 result rows, and all 135 had positive
signature overlap.

## How to identify affected output

Any KDA output generated with the old source checksum is affected and must be
rerun from the original inputs:

```text
15d1708803310bd66720e089ffb02a30352c1d1ef556602ed867e1662b86efa0
```

For Phase 12, inspect the `fKDA_source_sha256` column in `kda_status.tsv`.
Valid output from the corrected implementation must contain:

```text
fed8f89f35a3f08f38a420eb9b26c590cdc5f13a12064af1b9fa4a4cb1168550
```

Do not attempt to salvage affected output by filtering out only the rows with
`q = 0`. Because multiple-testing correction was performed using the faulty P
values, the entire KDA candidate set must be recalculated.

## Scope beyond Phase 12

The repository search found only one executable local implementation of
`predictKeyDrivers()`: `scripts/NetWeaver/fKDA.R`. Nevertheless, any external,
archived, or independently copied version should be checked for the literal
pattern:

```r
phyper(max(0, q - 1), ...)
```

or its vector-indexed equivalent. Results from a version containing that
boundary clamp should be considered affected until rerun with the corrected
formula.
