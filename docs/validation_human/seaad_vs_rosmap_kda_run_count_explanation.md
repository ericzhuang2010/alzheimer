# Why SEA-AD Has Fewer Runnable KDA Calls Than ROSMAP Phase 18
> **Historical note (superseded 2026-08-22):** This explanation describes the
> former five-donor/1.3-fold/coverage-0.80/q-0.05 SEA-AD run. For the current
> amended execution, see [seaad_thresholds.md](seaad_thresholds.md) and
> [vh09_vh10_execution_summary.md](vh09_vh10_execution_summary.md).


Yes, the SEA-AD KDA run count is substantially lower, but `84` is not directly
comparable to ROSMAP's primary count.

| Analysis | Runnable KDA runs |
|---|---:|
| ROSMAP Phase 18 primary, at least 10 genes | 161 |
| SEA-AD headline, at least 3 genes | 42 |
| SEA-AD headline, at least 10 genes | 21 |
| SEA-AD FDR-only sensitivity, at least 3 genes | 42 |
| SEA-AD total executed across both query rules | 84 |

The 84 calls are the same 42 biological direction slots analyzed under two
query definitions. The best primary comparison is therefore:

- SEA-AD headline: 42 versus ROSMAP: 161;
- under the same at-least-10-gene threshold: SEA-AD 21 versus ROSMAP 161.

SEA-AD starts with more structural slots—1,548 versus ROSMAP's 648—but
undergoes much greater attrition:

```text
1,548 structural SEA-AD directions
  ↓
1,028 retained as not estimable because the underlying contrast lacked donor support
  ↓
520 directions had DEG results
  ↓
462 had zero qualifying mitochondrial/network genes
16 had only 1-2 genes
  ↓
42 had at least 3 genes
  ↓
21 had at least 10 genes
```

## Why 1,028 direction slots were not estimable

One DEG contrast compares Dementia with No dementia within one:

```text
supertype + sex/APOE group
```

The frozen support gate required at least five profile-eligible donors in each
disease arm. A donor was profile-eligible for a supertype only when that donor
contributed at least 20 nuclei to the corresponding pseudobulk. The gate was
applied before edgeR fitting to avoid unstable estimates from extremely small
donor groups.

The full cohort's donor availability was already limiting:

| Group | Dementia donors | No-dementia donors | Supertype contrasts | Estimable | Not estimable |
|---|---:|---:|---:|---:|---:|
| `F_e2` | 1 | 6 | 129 | 0 | 129 |
| `F_e33` | 13 | 13 | 129 | 100 | 29 |
| `F_e4` | 9 | 5 | 129 | 68 | 61 |
| `M_e2` | 1 | 4 | 129 | 0 | 129 |
| `M_e33` | 9 | 10 | 129 | 92 | 37 |
| `M_e4` | 4 | 3 | 129 | 0 | 129 |
| **Total** |  |  | **774** | **260** | **514** |

Three groups could never pass the five-per-arm requirement, even before
considering supertype abundance:

- `F_e2` had only one Dementia donor;
- `M_e2` had only one Dementia donor and four No-dementia donors;
- `M_e4` had four Dementia and three No-dementia donors.

The other three groups had enough donors overall, but not every donor supplied
at least 20 nuclei for every supertype. This explains why 29 `F_e33`, 61
`F_e4`, and 37 `M_e33` supertype contrasts also failed the support gate.
`F_e4` was especially fragile because its No-dementia arm had exactly five
donors overall: if even one donor lacked 20 nuclei for a supertype, that
contrast became non-estimable.

The arithmetic behind 1,028 is therefore:

```text
514 unsupported supertype-by-group contrasts x 2 signed directions
    = 1,028 structural direction slots marked not_estimable
```

All 514 failures had the recorded reason `disease_arm_below_5`. There were no
additional fine-contrast failures from design rank, residual degrees of
freedom, edgeR fitting, or gene filtering. All 260 contrasts that passed donor
support completed successfully.

These 1,028 direction slots were not deleted and should not be interpreted as
showing no disease effect. They remain in the structural manifest as analyses
that the available donor support could not estimate reliably.

## Why the remaining completed directions produced few KDA queries

The main reasons are:

1. Only three of six groups produced estimable SEA-AD contrasts: `F_e33`,
   `F_e4`, and `M_e33`. The other groups generally lacked five donors in each
   disease arm at the supertype level.
2. Fine SEA-AD supertypes are often sparse. Splitting 78 donors across 129
   supertypes and six groups leaves many small donor strata.
3. Most completed contrasts had few significant core-mitochondrial genes.
   After FDR, effect-size, symbol-mapping, and network-intersection gates, 478
   of 520 completed directions remained below three genes.
4. ROSMAP produced more query-rich mitochondrial signatures. Phase 18 retained
   161 runs even under its stricter at-least-10-gene requirement.

The low run count is therefore caused by SEA-AD donor support and mitochondrial
DEG sparsity, not by having fewer structural cell-type slots or arbitrarily
limiting KDA.


## Should the SEA-AD donor threshold be lowered?

Yes, SEA-AD has substantially fewer donors than ROSMAP in the harmonized
analysis cohorts:

- SEA-AD: 78 donors;
- ROSMAP: 276 donors;
- SEA-AD therefore has about 28% as many donors as ROSMAP.

The six SEA-AD analysis groups have the following global donor counts:

| Group | Dementia | No dementia |
|---|---:|---:|
| `F_e2` | 1 | 6 |
| `F_e33` | 13 | 13 |
| `F_e4` | 9 | 5 |
| `M_e2` | 1 | 4 |
| `M_e33` | 9 | 10 |
| `M_e4` | 4 | 3 |

These are global cohort counts. The usable counts for an individual supertype
can be lower because a donor must contribute at least 20 nuclei to that
supertype's pseudobulk profile.

### Quantitative effect of a lower support threshold

Applying alternative donor thresholds to the existing fine-contrast manifest
gives:

| Minimum donors per disease arm | Donor-supported fine contrasts | Change from five | Maximum signed up/down query slots |
|---|---:|---:|---:|
| 5, current primary | 260 | -- | 520 |
| 4 | 279 | +19 | 558 |
| 3 | 382 | +122 | 764 |

The three-donor row is a support-based maximum, not the expected completed
total. One newly supported contrast, `L6b_5 x F_e33`, has three Dementia and
five No-dementia donors but a rank-deficient design. Therefore, 381 contrast
models, corresponding to at most 762 signed up/down query slots, are currently
model-feasible at the three-donor threshold.

Lowering the threshold to four has limited benefit and does not rescue the
`M_e4` group. Lowering it to three is the meaningful sensitivity option: it
adds 122 donor-supported contrast models relative to the primary threshold,
including 77 `M_e4` supertype contrasts.

### Recommendation

Retain at least five donors per arm as the primary analysis and add a separate,
clearly labeled sensitivity analysis requiring at least three donors per arm.
This preserves the statistically stronger primary results and Phase 18
comparison while allowing the smaller SEA-AD cohort to contribute additional
validation evidence.

Do not reduce the threshold below three. Neither `F_e2` nor `M_e2` can be
rescued by a two-donor threshold because each has only one Dementia donor in
the entire analysis cohort. A one-donor disease arm has no biological
replication and is not suitable for pseudobulk disease inference. More nuclei
from the same donor do not replace independent donors.

The three-donor sensitivity results should be written to a separate results
namespace and should report the exact case and reference donor counts for every
contrast. They should not overwrite or be pooled indiscriminately with the
five-donor primary results. Newly estimable DEG contrasts also will not
automatically become runnable KDA calls: each signed result must still pass the
DEG thresholds, symbol and network mapping, and minimum query-gene requirement.

The underlying counts and feasibility checks are recorded in:

- `results/validation_human/02_cohort/donor_group_counts.tsv`;
- `results/validation_human/07_contrasts/fine_contrast_manifest.tsv`;
- `results/validation_human/07_contrasts/design_rank_checks.tsv`;
- `results/minerva_production/02_cohort/cohort_status.tsv`.
