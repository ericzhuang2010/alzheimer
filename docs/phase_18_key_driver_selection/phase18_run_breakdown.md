# Phase 18 Run Breakdown

Phase 18 starts with 648 runs:

```text
54 fine cell types × 6 sex/APOE groups × 2 directions = 648 runs
```

The runs are divided as follows:

```text
648 total runs
│
├── 6 skipped
│      Reason: the source contrast was not estimable.
│      call_key_drivers() was not used.
│
├── 481 skipped
│      Reason: the effective query contained fewer than 10 genes.
│      call_key_drivers() was not used for Phase 18.
│
└── 161 included
       The effective query contained at least 10 genes.
       call_key_drivers() results were used for Phase 18.
```

| Phase 18 status | Reason | Runs |
|---|---|---:|
| Skipped | Source contrast was not estimable | 6 |
| Skipped | Effective query size was less than 10 | 481 |
| Included | Effective query size was at least 10 | 161 |
| **Total** |  | **648** |

## Eligible runs per driver class and broad network

There are **161 included runs in total**, but an ACAT calculation never uses
all 161. Each gene is aggregated within one broad network and one driver
class.

After merging the previous two mitochondrial cases, both driver classes have
the same fixed eligible-run count within a broad network:

```text
MT-driver eligible runs
    = all included runs in the broad network

non-MT-driver eligible runs
    = all included runs in that broad network
```

| Broad network | Total included runs | MT-driver eligible runs | non-MT-driver eligible runs |
|---|---:|---:|---:|
| Astrocytes | 21 | 21 | 21 |
| Excitatory neurons | 97 | 97 | 97 |
| Inhibitory neurons | 28 | 28 | 28 |
| Microglia | 6 | 6 | 6 |
| OPCs | 6 | 6 | 6 |
| Oligodendrocytes | 2 | 2 | 2 |
| Vasculature cells | 1 | 1 | 1 |
| **All broad networks** | **161** | **Network-specific; not summed for one gene** | **Network-specific; not summed for one gene** |

For an excitatory-neuron gene in either class:

```text
eligible_run_count = 97
```

For an MT driver, query membership still determines whether self-overlap is
removed in an individual run. It no longer changes the aggregate class or its
eligible-run denominator.

Therefore, the `eligible_run_count` column is a
**gene × broad-network × driver-class denominator**, not the global number
161.

## Genes tested in the 161 included calls

Of the 161 included `call_key_drivers()` calls:

- all 161 calls explicitly tested at least one candidate gene;
- 95,557 explicit gene × run tests were performed;
- 6,149 unique gene symbols were tested;
- 122 calls returned at least one significant gene;
- 39 calls returned no significant genes;
- 1,641 significant gene × run rows were returned in total; and
- these 1,641 rows represented 295 unique gene symbols.

A gene can be tested in more than one run. Therefore, 95,557 is the number of
tested gene × run rows, whereas 6,149 is the number of distinct tested genes.

The 1,641 significant rows are a subset of the 95,557 tested rows. The complete
table is
[`call_key_driver_returns.tsv`](../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv).
The significant-only provenance table is
[`call_key_driver_significant_returns.tsv`](../../results/minerva_production/18_key_driver_selection/call_key_driver_significant_returns.tsv).
