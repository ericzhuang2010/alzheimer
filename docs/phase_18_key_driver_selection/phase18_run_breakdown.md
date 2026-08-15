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

## Genes returned for the 161 included calls

Of the 161 included `call_key_drivers()` calls:

- 122 calls returned at least one significant gene;
- 39 calls returned no significant genes;
- 1,641 significant gene × run rows were returned in total; and
- these 1,641 rows represented 295 unique gene symbols.

A gene can be returned in more than one run. Therefore, 1,641 is the number of returned gene × run results, whereas 295 is the number of distinct genes across all 161 calls.

These are only the genes that passed the original within-run significance threshold. They are not all genes tested by KDA.
