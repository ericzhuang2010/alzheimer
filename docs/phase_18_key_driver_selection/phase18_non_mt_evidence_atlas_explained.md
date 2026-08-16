# Phase 18 non-MT-driver evidence atlas: figure guide

## Figure and scope

This document explains the
[Phase 18 non-MT-driver evidence atlas](../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt.png).
The current driver class is `non_mt_driver`.

The figure summarizes:

- 15 selected non-MT genes;
- 21 gene-by-broad-network contexts displayed in the circular figure;
- 22 total passing gene-by-broad-network contexts; and
- 161 included KDA calls.

Non-MT means that the driver is outside the fixed 1,136-gene core MitoCarta
inventory. It does not prove that the gene has no mitochondrial function.

## Important terms

### KDA run

One run is one:

```text
fine cell type × sex/APOE group × AD signature direction
```

The query is the effective set of upregulated or downregulated MT genes for
that combination. Each run belongs to exactly one broad cell-type network.

### Eligible run

Eligibility is a property of the run. An eligible run has a validated source
contrast, a usable induced Bayesian network and an effective query containing
at least 10 genes. The current analysis includes 161 completed eligible calls.

### Explicitly tested gene

Testing is a property of a particular gene within a run. Starting from the
run-specific effective MT query, `call_key_drivers()`:

1. finds candidate genes within three undirected network layers of the query;
2. constructs each candidate's directed downstream neighborhoods, up to three
   layers; and
3. calculates an enrichment P value when at least one directed neighborhood
   can be evaluated.

Thus, a gene is explicitly tested when it is in the three-layer candidate
family and has a directed neighborhood that can be evaluated.

Within an eligible run, a gene can have one of three states:

| Gene state | Treatment in Phase 18 |
|---|---|
| Explicitly tested | A run-specific enrichment P value is calculated |
| In the effective background but not explicitly tested | An implicit P value of 1 is used for ACAT |
| Absent from the effective background | The gene is missing for that run |

Every row of
[`call_key_driver_returns.tsv`](../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv)
is one explicitly tested gene-by-run combination. Therefore, the presence of a
`kda_run_id + key_driver` row means the gene was tested in that run. Absence of
a row does not mean the run was ineligible; the gene may instead have been
implicit or missing.

### Significant KDA return

A tested gene is a significant KDA return when
`significant_by_call_key_drivers = TRUE`, corresponding to the original
within-run BH-adjusted P value being at most 0.05.

### Conservative support

A significant tested gene provides conservative support only when all of the
following also hold:

- at least two other query genes overlap the driver's neighborhood;
- fold enrichment is greater than 1; and
- `final_run_q ≤ 0.05`.

Conservative-support runs are therefore a subset of significant KDA returns.

## Panel A: network evidence matrix

Panel A shows the final gene-by-broad-network results.

- Rows are the 15 selected genes.
- Columns are the seven broad cell-type networks.
- A filled tile means that the gene passed final driver selection in that
  network.
- Tile fill represents capped `-log10(aggregate_acat_q)`. Brighter values
  indicate smaller aggregate q values.
- The number inside a tile is the within-network non-MT-driver rank.
- A solid border means the context was among the five genes displayed for that
  network in the circular figure.
- A dashed border means the context passed but fell below the five-gene display
  cap.
- A diamond beside a symbol marks membership in the broader mitochondrial
  reference.

The dashed RPS15 tile in Excitatory neurons has rank 20. It passed final
selection but was not displayed in that network's top five. The five-gene rule
is a display cap, not a significance threshold.

Panel A is gene by broad network. It does not show how many individual KDA
runs returned the gene.

## Panel B: run occurrence and evidence breadth

Panel B summarizes each selected gene across all included `non_mt_driver` KDA
calls in which that gene was explicitly tested. It is not restricted to the
broad networks in which the gene ultimately passed final selection.

### 1. Significant KDA runs / tested runs

```text
significant KDA run count
  = number of explicit gene-by-run rows with
    significant_by_call_key_drivers = TRUE

tested run count
  = number of unique kda_run_id values with an explicit row for the gene
```

For example, `29/84` for RPL11 means that RPL11 was explicitly tested in 84
unique calls and returned as significant in 29 of them.

A gene can be tested in multiple broad networks. Because every run belongs to
one broad network, summing its tested runs across networks does not double
count any run.

RPL11 has the following distribution:

| Broad network | Explicitly tested runs | Significant runs |
|---|---:|---:|
| Astrocytes | 13 | 3 |
| Excitatory neurons | 58 | 24 |
| Inhibitory neurons | 7 | 0 |
| Microglia | 4 | 1 |
| OPCs | 0 | 0 |
| Oligodendrocytes | 1 | 1 |
| Vasculature | 1 | 0 |
| **Total** | **84** | **29** |

Eligible and tested are not interchangeable. For example, within the
Excitatory-neuron network, RPL11 has:

| Run category | Count |
|---|---:|
| Eligible runs | 97 |
| Explicitly tested | 58 |
| In the background but implicit P = 1 | 39 |
| Missing from the background | 0 |
| Significant among the 58 explicit tests | 24 |

### 2. Conservative support / tested runs

This track reports:

```text
number of conservative-support runs / number of explicitly tested runs
```

For example, `25/84` for RPL11 means that 25 of its 84 explicit tests met all
conservative-support conditions. This distinguishes a raw significant return
from the stricter evidence used by Phase 18.

### 3. Supporting fine cell types

For each gene:

```text
supporting_fine_cell_type_count
  = number of distinct fine_cell_type values among
    conservative_support = TRUE rows
```

A fine cell type is counted once even if the gene has conservative support in
several sex/APOE groups, AD directions or runs for that fine cell type.

The label `observed range 1–18` describes the range among the 15 selected genes.
It is not the total possible number of fine cell types. The 161 included calls
span 34 distinct fine cell types:

- 3 astrocyte types;
- 14 excitatory-neuron types;
- 12 inhibitory-neuron types;
- 2 microglial types;
- 1 OPC type;
- 1 oligodendrocyte type; and
- 1 vascular type.

RPS15 has the largest observed breadth, with conservative support in 18 fine
cell types. It was explicitly tested in 30 fine cell types. RPL11 has support
in 15 of the 25 fine cell types in which it was explicitly tested.

### 4. Passing networks

This is the number of broad networks in which the gene has
`terminal_candidate_status = driver_candidate`. The maximum is seven. A gene
can contribute at most one final candidate result per broad network because
selection aggregates to one gene-by-broad-network record.

### 5. Sex/APOE groups

This is the number of distinct primary `signature_group` values among the
gene's conservative-support runs. The maximum is six. It is an evidence-breadth
summary, not a statistical interaction test.

### 6. AD directions

This is the number of distinct directions among conservative-support runs:

```text
AD_up_mito
AD_down_mito
```

The maximum is two. A value of two means that conservative support occurred
for both upregulated and downregulated MT queries.

### Provenance of nonsignificant tested results

The original `call_key_drivers()` output saved only significant genes. The
Phase 18 export script reconstructs the complete table before the final FDR
filter from the original queries, backgrounds and Bayesian networks. It checks
that the reconstructed significant subset matches all 1,641 originally saved
significant gene-by-run rows. The current all-tested table contains 95,557
explicit tests: 1,641 significant and 93,916 nonsignificant.

## Panel C: network stability

Panel C asks whether each passing gene-by-broad-network result depends strongly
on one fine cell type.

For every passing context:

1. remove all runs from one fine cell type;
2. recalculate coverage, conservative support, ACAT P/q, candidate status and
   within-class ranking; and
3. repeat for every fine cell type in that broad network.

Each colored point represents one passing gene-by-broad-network context.
Colors match Panel A. A gene that passes in multiple broad networks can have
multiple points on its row; the points are slightly offset vertically so they
remain visible.

### Candidate retention

```text
candidate retention
  = assessable omissions retaining driver_candidate status
    / all assessable omissions
```

- `1.0` means the gene remained a driver candidate after every assessable
  fine-cell-type omission.
- `0.8` means it remained a candidate after 80% of omissions.
- `0.5` means it remained a candidate after half of the omissions.
- `0` means it failed after every assessable omission.

The dotted line at 0.8 is a visual stability reference, not a Phase 18
selection gate.

### Worst rank

Worst rank is the largest within-network non-MT-driver rank observed among
omission analyses where a rank could be assigned.

- Rank 1 is best; lower is more stable.
- The dotted line at rank 5 marks the circular figure's display cap.
- Values greater than 25 are plotted at 25.

Candidate retention and worst rank must be read together. If a gene loses
candidate status after an omission, no rank may be assigned for that omission.
The worst-rank track then summarizes only the omissions where a rank exists.

For example, RPL11 in Astrocytes has retention `2/3 = 0.67`. It remained rank
1 in the two omissions where it retained candidate status, but failed
candidate selection after the other omission. Its rank point is therefore 1,
while the retention point shows the instability.

### RPS15 example

| Broad network | Assessable omissions | Candidate retention | Worst rank |
|---|---:|---:|---:|
| Excitatory neurons | 14 | 13/14 = 0.93 | 21 |
| Inhibitory neurons | 12 | 12/12 = 1.00 | 1 |
| OPCs | 0 | Not assessable | Not assessable |

RPS15 is stable as an Inhibitory-neuron candidate. Its Excitatory-neuron
candidate status is retained in most omissions, but its rank remains below the
circle's five-gene display cap.

### `×` marks

An `×` means that leave-one-fine-cell-type stability was not assessable. It
does not mean zero retention or rank 1. This commonly occurs when a broad
network contains only one included fine cell type: removing it would leave no
runs for recalculation. OPC, Oligodendrocyte and Vasculature contexts are
typical examples.

Panel C is a post-selection robustness diagnostic. It did not determine which
genes passed the original Phase 18 selection.

## Interpretation limits

- Panel B run counts are repeated evidence contexts within the study, not
  independent external replications.
- Sex/APOE-group and direction counts describe breadth; they do not test
  interactions or group differences.
- The circle's top-five rule controls display only.
- A Bayesian-network key-driver association is not experimental proof that the
  gene causally regulates the query genes.
- Panel C should be used to distinguish broadly stable candidates from results
  driven by a small number of fine cell types, not to create a new combined
  score.

## Related files

- [Gene summary table](../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt_gene_summary.tsv)
- [Gene-network detail table](../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt_gene_network_details.tsv)
- [Figure caption](../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt_caption.md)
- [Figure methods](../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt_methods.md)
- [Figure-generation script](../../scripts/figures/analysis/phase_18_key_driver_selection/plot_phase18_non_mt_evidence_atlas.py)
