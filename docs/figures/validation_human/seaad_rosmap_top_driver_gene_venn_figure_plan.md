# SEA-AD–ROSMAP Top-Driver Gene Venn Figure

> **Historical figure specification (superseded 2026-08-23):** The generated
> assets were not rebuilt for the coverage-0.80/q-0.05 selection-only rerun.
> Current analytical results are in
> [vh09_vh10_execution_summary.md](../../validation_human/vh09_vh10_execution_summary.md).


## Status

**Implemented and validated on 2026-08-20.**

Figure/package ID: `seaad_rosmap_top_driver_gene_venn`

## Purpose

Produce one two-panel set-comparison figure for the selected top key-driver
genes from ROSMAP Phase 18 and SEA-AD:

- panel A: `mt_driver` genes; and
- panel B: `non_mt_driver` genes.

Each gene is counted once per cohort and driver class after collapsing broad-
network membership. The figure must print every common and cohort-only gene,
not only the region counts.

This is a secondary, descriptive gene-symbol comparison. The primary
rediscovery analysis remains the strict `broad_network + gene + driver_class`
comparison within the common assessable universe.

## Main message

> All six SEA-AD MT top-driver genes also occur somewhere in the ROSMAP Phase
> 18 MT top-driver set, whereas the selected non-MT gene sets are disjoint.

The MT result is true set containment, not a conventional three-region Venn:
SEA-AD contributes no MT-only gene. The non-MT result has no intersection.
The geometry must therefore show nested MT circles and separated non-MT
circles rather than imply regions that contain no genes.

## Set definition

### ROSMAP

Read the frozen Phase 18 selected units:

```text
results/validation_human/09_rosmap_kda_candidates/
  phase18_selected_candidate_units.tsv
```

Keep `top5_display = True`, split by exact `case_id`, and deduplicate
`key_driver` across broad networks.

### SEA-AD

Read the independently frozen SEA-AD top lists:

```text
results/validation_human/10_seaad_kda_rediscovery/
  10c_seaad_selection/seaad_top5.tsv
```

Keep only `list_status = ranked_candidates` for
`query_rule_id = phase18_parity_query` and
`result_tier_id = phase18_parity_query__min3_all`, split by exact `case_id`,
and deduplicate `current_symbol` across broad networks. Sentinel rows with
`current_symbol = NA` are not genes.

### Driver classes

- `mt_driver` means membership in the frozen Phase 18 core-MitoCarta set.
- `non_mt_driver` means every other assessable network gene.
- MT is not synonymous with mtDNA encoded.
- Query membership does not define a third class.

Never identify MT rows using a substring match because `non_mt_driver`
contains the text `mt_driver`; class matching must be exact.

## Frozen regions and gene labels

| Driver class | ROSMAP genes | SEA-AD genes | ROSMAP only | Common | SEA-AD only |
|---|---:|---:|---:|---:|---:|
| MT | 10 | 6 | 4 | 6 | 0 |
| Non-MT | 15 | 5 | 15 | 0 | 5 |

### Panel A — MT drivers

ROSMAP only:

```text
COX4I1, COX6B1, COX7C, UQCR10
```

Common after collapsing network identity:

```text
MT-ATP6, MT-CO2, MT-CO3, MT-CYB, MT-ND4, MT-ND5
```

SEA-AD only:

```text
none
```

The SEA-AD circle is completely contained by the ROSMAP circle. MT-ATP6 and
MT-ND4 are common at gene level but were selected in different broad networks
between the cohorts; they are not strict same-network rediscoveries.

### Panel B — Non-MT drivers

ROSMAP only:

```text
ANKRD11, APOE, ATP6V1F, DYNLT1, FTL,
LAMTOR5, LAPTM4A, NCOA1, RPL11, RPL15,
RPL38, RPLP1, RPS13, RPS15, SELENOW
```

Common:

```text
none
```

SEA-AD only:

```text
BEX3, HGSNAT, KANSL1L, RPL30, RPS27A
```

The two circles are disjoint. ANKRD11, FTL, and NCOA1 are ROSMAP OPC-only
selections; SEA-AD had no included OPC KDA run. Their absence from SEA-AD is
not a tested negative result.

## Visual design

### Canvas

- One 12 × 7.2 inch white canvas.
- Two equal-width panels with bold panel labels `A` and `B`.
- Export a searchable SVG, vector PDF, and 5400 × 3240 PNG at 450 DPI.
- Overall title: `Gene-level overlap of selected top key drivers`.
- Subtitle: `Unique symbols; broad-network membership collapsed`.
- Panel A title: `MT driver class` with the visible qualifier
  `Phase 18 core MitoCarta; not mtDNA-only`.
- Panel B title: `Non-MT driver class`.

### Geometry

Use native Matplotlib circle patches; do not add a `matplotlib-venn`
dependency. Circle area is proportional to the number of unique genes with
one shared scale across both panels:

```text
radius(n) = 0.43 × sqrt(n)
```

- MT: nest the six-gene SEA-AD circle completely inside the ten-gene ROSMAP
  circle.
- Non-MT: separate the 15-gene ROSMAP and five-gene SEA-AD circles.
- Freeze the MT centers at ROSMAP `(0, 0)` and SEA-AD `(0.25, 0)`, with panel
  limits `x = [-2.2, 2.2]`, `y = [-1.8, 2.0]`.
- Freeze the non-MT centers at ROSMAP `(-1.55, 0)` and SEA-AD `(1.25, 0)`,
  with panel limits `x = [-3.35, 2.55]`, `y = [-1.9, 1.95]`.
- Record every center and radius in `region_summary.tsv`; validate
  `center_distance + r_SEA <= r_ROSMAP` for MT and
  `center_distance >= r_ROSMAP + r_SEA` for non-MT.
- Use equal-aspect axes and state `Area proportional to unique-gene count`.
- Print `SEA-AD only: 0 (∅)` directly in panel A.
- Print `Common: 0 (∅)` and `No shared top-list gene` directly between the
  circles in panel B.

Names are alphabetical within each region. There is no honest single rank
after deduplicating per-network top-five lists, so rank must not control label
order or typography.

### Cohort encoding

Use color and redundant outline/texture:

| Set | Fill | Border | Redundant encoding |
|---|---|---|---|
| ROSMAP Phase 18 | pale blue `#DCEEF7` | solid blue `#0072B2` | solid 1.5-point outline |
| SEA-AD | pale orange `#FBE6C5` | vermilion `#D55E00` | dashed outline and diagonal hatch |
| MT common/contained region | pale purple `#E8DCEB` | SEA-AD outline | direct `Common • 6` label |

Every set and region also has a direct text label and count, so the figure
remains interpretable in grayscale.

### Label placement

- MT ROSMAP-only genes: a leader-linked outside callout anchored to the narrow
  exposed ROSMAP crescent; never squeeze four labels into that crescent.
- MT common genes: two columns × three rows inside the contained SEA-AD
  circle.
- Non-MT ROSMAP-only genes: three columns × five rows inside the ROSMAP
  circle.
- Non-MT SEA-AD-only genes: one column inside the SEA-AD circle.
- Minimum visible font at native size: 8 points for gene names and 7 points
  for explanatory footnotes.

Visible footer:

```text
Descriptive gene-level view • networks collapsed • no overlap P value
```

Add a dagger to ANKRD11, FTL, and NCOA1 with a visible/caption key
`SEA-AD OPC KDA unavailable`. Explain in the caption that MT-ATP6 and MT-ND4
are gene-level-only common genes without a strict same-network match.

## Interpretation guardrails

1. Circle counts are unique gene symbols, not network–gene units.
2. The ROSMAP 47 selected units collapse to 25 genes: 10 MT and 15 non-MT.
3. The SEA-AD 13 selected units collapse to 11 genes: 6 MT and 5 non-MT.
4. `Common` means selected in any network in both cohorts within the same
   driver class.
5. Common gene identity does not require a strict same-network match.
6. Cohort-only does not mean failed replication, absent biology, or opposite
   regulation; network testability differs.
7. No inferential P value is attached to this descriptive gene-only view.
8. Top five is a per-network maximum; lists were not backfilled.

## Authoritative inputs and validation

| Purpose | File |
|---|---|
| ROSMAP completion | `results/validation_human/09_rosmap_kda_candidates/status.tsv` |
| ROSMAP registered hashes | `.../09_rosmap_kda_candidates/artifacts.tsv` |
| ROSMAP selected units | `.../09_rosmap_kda_candidates/phase18_selected_candidate_units.tsv` |
| SEA-AD completion | `.../10c_seaad_selection/status.tsv` |
| SEA-AD registered hashes | `.../10c_seaad_selection/artifacts.tsv` |
| SEA-AD selected lists | `.../10c_seaad_selection/seaad_top5.tsv` |
| Independent SEA-AD freeze | `.../10c_seaad_selection/seaad_selection_freeze.tsv` |
| Overlap completion | `.../10d_overlap/status.tsv` |
| Overlap registered hashes | `.../10d_overlap/artifacts.tsv` |
| Class-specific unit cross-check | `.../10d_overlap/rosmap_seaad_candidate_overlap.tsv` |
| Gene-only cross-check | `.../10d_overlap/rosmap_seaad_gene_only_overlap.tsv` |
| Overlap checks | `.../10d_overlap/overlap_checks.tsv` |

Required registered data-artifact SHA-256 values include:

- ROSMAP selected units:
  `e758720f7dcd80d1d6ef72fc7f95bfa20e3784931114e59c716a0e85b681d443`;
- SEA-AD top list:
  `18b4cdd6cbadbf4ef741cdf54cf2dd992017035786726d701a5d818acc3937ac`;
- class-specific overlap:
  `68b839ef1dae967bc482d16667d94fe8fd2a8bb17290ea43b2a96767c4abbfa6`;
  and
- gene-only overlap:
  `8b71aef2aa561ef33e1ad679a96dc2fc48c674a76a89c09a4ac3cfb735341e16`.

Registered data artifacts must match their manifest hashes. Phase status,
artifact manifests, the SEA-AD freeze, and compact check tables instead
satisfy explicit semantic and, where specified, fixed-hash checks; a phase
manifest is not expected to register itself. The renderer validates only the
compact files required for this display. The
locally absent full candidate/universe intermediates are not required and the
figure must not claim to recompute either cohort's complete candidate
selection.

## Implementation contract

Renderer:

```text
scripts/figures/validation_human/plot_seaad_rosmap_top_driver_gene_venn.py
```

Automated test:

```text
tests/validation_human/test_seaad_rosmap_top_driver_gene_venn.py
```

Output directory:

```text
results/figures/validation_human/seaad_rosmap_top_driver_gene_venn/
```

The package contains ten files:

```text
seaad_rosmap_top_driver_gene_venn.png
seaad_rosmap_top_driver_gene_venn.pdf
seaad_rosmap_top_driver_gene_venn.svg
seaad_rosmap_top_driver_gene_venn_plot_data.tsv
seaad_rosmap_top_driver_gene_venn_region_summary.tsv
seaad_rosmap_top_driver_gene_venn_caption.md
seaad_rosmap_top_driver_gene_venn_methods.md
seaad_rosmap_top_driver_gene_venn_checks.tsv
seaad_rosmap_top_driver_gene_venn_artifacts.tsv
seaad_rosmap_top_driver_gene_venn_status.tsv
```

The renderer writes to a staging directory, validates the staged package, and
atomically publishes it. The artifact manifest hashes the eight payload files,
the authoritative inputs, and the renderer. It excludes itself and the later-
written status file.

The canonical package was published after manual color and grayscale review.
Its status records `validation_status = validated_complete` and
`visual_review_status = complete`.

## Automated validation contract

Publication is blocked unless:

- VH09, VH10C, and VH10D report `validated_complete` with no failed checks;
- all locally consumed inputs match their registered full-file hashes;
- the SEA-AD freeze records `rosmap_candidate_files_read = False`;
- selected-unit counts are ROSMAP 47 and SEA-AD 13;
- unique-gene counts are ROSMAP 25 and SEA-AD 11;
- no gene is assigned to both driver classes within a cohort;
- the plot table contains exactly 30 unique `case_id + gene` rows;
- the region-summary table contains exactly six rows, including MT SEA-only
  and non-MT common rows with count zero;
- region counts are exactly MT `4 / 6 / 0` and non-MT `15 / 0 / 5`;
- region gene identities exactly match the frozen lists above;
- the class-specific and gene-only VH10D tables reproduce the derived sets;
- circles have one common area-per-gene scale and exact nested/disjoint logic;
- all 30 genes and both empty-set (`∅`) labels occur as searchable SVG text;
- all three image exports exist and are nonempty;
- PNG size and embedded resolution are 5400 × 3240 and approximately 450 DPI;
- SVG contains searchable text and vector paths, and PDF has a valid signature;
- every declared payload/input/script hash validates; and
- final status is written last as `validated_complete` only after color and
  grayscale visual review is complete.

## Draft caption

**Gene-level overlap of selected ROSMAP Phase 18 and SEA-AD key drivers.**
Selected top-driver symbols were deduplicated across broad-network top-five
lists within each driver class. The MT diagram shows exact containment: all
six SEA-AD MT genes occurred somewhere in the ten-gene ROSMAP MT set, while
four MT genes were ROSMAP only. The non-MT sets were disjoint: 15 ROSMAP genes
and five SEA-AD genes with no shared symbol. Circle area is proportional to
unique-gene count. This descriptive comparison ignores network identity and
has no overlap P value; strict replication is defined separately by broad
network, gene, and driver class within the common assessable universe.

## Draft source line

```text
Source: validated VH09 ROSMAP Phase 18 and independently frozen VH10C SEA-AD top-driver lists; VH10D overlap cross-check.
```
