# Plan for the mitochondrial KDA workflow figure

## 1. Figure purpose

Create one self-contained methods figure that explains how validated
mitochondrial AD-versus-NCI signatures are turned into cell-type-specific
putative key drivers. The figure should make the distinction between the
**primary** and **secondary** analyses immediately visible, while also showing
that both branches use the same run-specific network construction,
eligibility rules, and directed NetWeaver enrichment test.

This should be a companion to the existing NetWeaver circular results figure.
The circular figure summarizes recurrent significant drivers; the proposed
figure explains how the underlying KDA runs were defined and tested.

Recommended title:

```text
Cell-type-specific mitochondrial key-driver analysis
```

Recommended one-sentence takeaway:

> Mitochondrial AD signatures from individual sex/APOE strata and prespecified
> pooled summaries were tested separately for enrichment in directed,
> cell-type-matched Bayesian-network neighborhoods.

## 2. Recommended overall composition

Use a landscape, left-to-right workflow with four main panels and a narrow
production-outcome ribbon along the bottom:

```text
┌──────────────────┐   ┌──────────────────────────────┐
│ A. Frozen inputs │ → │ B. Analysis grid             │
│                  │   │ ┌ Primary ┐  ┌ Secondary ┐   │
└──────────────────┘   │ └─────────┘  └───────────┘   │
                       └──────────────┬───────────────┘
                                      ↓
┌──────────────────────────────────────────────────────┐
│ C. Construct one run: signature + induced network   │
└──────────────────────────┬───────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────┐
│ D. Directed KDA test → putative key drivers          │
└──────────────────────────────────────────────────────┘

Production outcome: 1,782 planned → 1,021 eligible →
840 with ≥1 significant driver; 761 skipped; 0 failed
```

Panels A and B should occupy the upper half of the figure. Panels C and D
should form the lower analytical workflow. The bottom ribbon reports the
validated production outcome without turning the methods figure into a
results-ranking plot.

## 3. Panel A — frozen inputs and cell-type/network mapping

### Main message

The KDA workflow inherits validated differential-expression calls,
mitochondrial annotations, and final directed Bayesian networks. It does not refit the
differential-expression model or rebuild the networks.

### Visual content

Draw three input blocks converging on the analysis-grid panel:

1. **Stratified AD-versus-NCI differential expression**
   - 54 fine cell types;
   - six sex/APOE contrasts per fine cell type;
   - effect direction is AD minus NCI; and
   - retain the validated `paper_deg` calls.
2. **Validated mitochondrial annotation**
   - required universe: `core_mito_protein`;
   - use the original assay identifier for network matching; and
   - do not rebuild mitochondrial membership from gene-name prefixes.
3. **Nine final directed Bayesian networks**
   - arrows point from upstream to downstream;
   - each fine cell type maps to exactly one broad cell-class network; and
   - related fine cell types can reuse a broad network but remain separate
     analyses.

Use a small mapping example to make the two cell-type scales concrete:

```text
Mic P2RY12 fine-cell signature → Microglia broad Bayesian network
```

Label the distinction explicitly:

```text
signature scope = fine cell type
network scope   = broad cell class
```

Avoid drawing the nine networks as one merged graph. A stack of nine small
directed-network icons is sufficient.

## 4. Panel B — primary and secondary analysis grid

This is the visual center of the figure. Use two parallel, clearly labeled
lanes that later converge on Panel C.

### Panel B1: primary analyses

Use six individual group cards:

```text
Female e2     Female e33     Female e4
Male e2       Male e33       Male e4
```

The production field labels may be shown in smaller type below the display
labels:

```text
F_e2, F_e33, F_e4, M_e2, M_e33, M_e4
```

For every fine cell type, keep all six AD-versus-NCI contrasts separate. From
each contrast construct exactly three core-mitochondrial signatures:

```text
AD-up:   D_up
AD-down: D_down
Both:    D_both = D_up ∪ D_down
```

Show the primary grid arithmetic prominently:

```text
54 fine cell types × 6 strata × 3 signatures = 972 planned runs
```

The figure should visually reinforce that primary analyses are the main
scientific results and that no information is pooled before these signatures
are tested.

### Panel B2: secondary analyses

Show five pool cards, each connected to its required primary source groups:

| Secondary pool | Required source groups |
|---|---|
| Female pool | `F_e2`, `F_e33`, `F_e4` |
| Male pool | `M_e2`, `M_e33`, `M_e4` |
| e2 pool | `F_e2`, `M_e2` |
| e33 pool | `F_e33`, `M_e33` |
| e4 pool | `F_e4`, `M_e4` |

For a complete pool, show the signature rule as a set union of the member
DEG calls:

```text
P_up   = union of member D_up sets
P_down = union of member D_down sets
P_both = P_up ∪ P_down
```

Place the following short annotation directly inside the secondary lane:

```text
Prespecified set-union summary — not a newly fitted pooled DE contrast
```

Also include a small two-color gene example showing that a gene can be AD-up
in one source group and AD-down in another. Label it
`direction-discordant`; it may occur in both pooled directional signatures
but appears once in `P_both`.

Show the secondary grid arithmetic prominently:

```text
54 fine cell types × 5 pools × 3 signatures = 810 planned runs
```

A small gate at the entrance to the secondary lane should state:

```text
All required source contrasts must be validated
```

If one source is unavailable or non-estimable, the pool is marked incomplete;
the available members are not silently pooled.

### Panel B3: complete grid

Where the two lanes converge, show:

```text
972 primary + 810 secondary = 1,782 planned runs
```

Define one run in small type as:

```text
fine cell type × analysis tier × group × signature direction
× core-mito profile × frozen KDA profile
```

## 5. Panel C — construction and eligibility of one KDA run

### Main message

Each run receives its own effective query, induced network, and background.
Two signatures mapped to the same broad network can therefore still have
different KDA inputs.

### Recommended schematic

Use one enlarged example run and depict three successive operations.

#### Step C1: candidate mitochondrial query

Start with one of the three candidate signatures from Panel B:

```text
candidate query Q0 = AD-up, AD-down, or both core-mito DEGs
```

#### Step C2: exact tested genes and induced network

Show the background rule separately for the two analysis tiers:

- **Primary:** genes returned by MAST in the exact fine-cell-type/stratum
  contrast.
- **Secondary:** intersection of genes tested in every required pool member.

For the secondary branch, draw an intersection symbol rather than a union
symbol. This is an important distinction:

```text
pooled query      = union of member DEG calls
pooled tested set = intersection of member tested-gene sets
```

Next, restrict the matching broad Bayesian network to edges whose two
endpoints occur in the exact tested set. Remove isolated nodes after edge
restriction. The remaining directed graph is the run-specific induced
network, and its unique nodes are the effective background `B`.

#### Step C3: effective query and eligibility

Show:

```text
Q = Q0 ∩ B
```

Then use a decision diamond with the following ordered checks:

1. all source contrasts are validated;
2. the induced network contains at least one edge; and
3. the effective query contains at least three genes.

Eligible runs proceed to Panel D. Ineligible runs stay in the run manifest
with an explicit reason. A query of 3–9 genes proceeds but carries a small
query warning.

Display the main skip labels in a small gray callout:

```text
source contrast/pool incomplete
background network empty
effective query < 3
```

Do not use the presence of a significant driver as an eligibility rule.

## 6. Panel D — directed NetWeaver KDA test

### Main message

For each eligible run, NetWeaver asks whether the effective mitochondrial
query is unusually concentrated in a candidate driver's directed downstream
neighborhood.

### Network illustration

Draw a small directed acyclic graph containing:

- one candidate upstream driver as a large outlined node;
- arrowheads pointing downstream;
- cumulative first-, second-, and third-layer neighborhoods shown as nested
  translucent regions;
- effective query genes highlighted within the graph; and
- non-query background genes in neutral gray.

The example should make clear that the algorithm tests downstream
neighborhoods up to three layers and retains the best layer for each candidate
driver.

### Statistical inset

Define the four counts visually:

| Symbol | Meaning |
|---|---|
| `M` | total effective-background genes |
| `m` | genes in the selected driver neighborhood |
| `k` | effective mitochondrial query genes |
| `q` | query genes inside the selected neighborhood |

Show the enrichment ratio:

```text
fold enrichment = (q / m) / (k / M) = qM / mk
```

Below it, state:

```text
One-sided hypergeometric enrichment
BH correction across candidate drivers within this run
significant if adjusted P ≤ 0.05
```

Add a compact parameter strip:

```text
directed = TRUE | layers tested = 1–3 | signature expansion = 0
global-driver reduction distance = 2 | overlap genes returned
```

### Output

End the panel with a short result card:

```text
Putative key driver / candidate upstream regulator
best layer • overlap genes • fold enrichment • adjusted P value
```

If no candidate passes the cutoff, display
`completed — no significant key driver`; this is a valid result, not a
failure.

## 7. Production-outcome ribbon

Use the validated KDA production values, with precise denominators:

```text
54 fine cell types
9 broad networks
1,782 planned runs
1,021 eligible runs
761 skipped runs
0 failed runs
840 eligible runs with ≥1 significant driver
10,172 significant driver rows
validation: complete; 11/11 checks passed
```

Recommended flow for the run counts:

```text
1,782 planned
├── 1,021 eligible
│   ├── 840 with ≥1 significant driver
│   └── 181 with no significant driver
└── 761 skipped with explicit reason

0 failed
```

The value 181 is derived as `1,021 - 840` and should either be calculated by
the figure script or omitted if the figure reports only stored values.

Do not label the 10,172 rows as 10,172 unique drivers. They are significant
driver-by-run result rows. CAMs and T cells may be mentioned in the caption as
having no eligible production KDA run; this is an input-eligibility outcome,
not evidence that those networks lack biological drivers.

## 8. Visual language

Use a limited, color-blind-aware palette and combine color with labels and
shape so that the logic remains clear in grayscale.

| Concept | Suggested treatment |
|---|---|
| Frozen inputs and background genes | neutral gray |
| Primary branch | dark teal with solid border |
| Secondary branch | purple with double or dashed border |
| AD-up signature | vermilion/red-orange upward triangle |
| AD-down signature | blue downward triangle |
| AD-both signature | paired red/blue marker or split circle |
| Effective query genes | saturated gold nodes with dark outline |
| Candidate driver | white or dark node with heavy outline |
| Ineligible/skipped path | light gray, dashed arrow |
| Validated output | green check mark used sparingly |

Use solid arrows for data flow and arrowheads on all network edges. Use union
and intersection symbols only where the corresponding set operation is
scientifically intended. The words **Primary** and **Secondary pooled
summary** should remain visible even if all color is removed.

Avoid dense screenshots of tables. The figure should explain the analysis
through icons, concise equations, and a single representative network.

## 9. Required interpretation guardrails

Include these statements in the caption or as a compact footer:

1. Secondary pools reuse primary-group information and are not independent
   biological replications.
2. A pooled signature is a set-union summary, not a newly fitted pooled
   differential-expression contrast.
3. Bayesian-network direction and neighborhood enrichment prioritize
   putative upstream regulators; they do not prove causality, activation, or
   inhibition.
4. BH adjustment is performed within one KDA run, not across all 1,782
   planned runs.
5. `global_key_driver` is a within-run redundancy-reduction flag, not evidence
   that a driver is globally significant across the study.
6. Primary stratum-specific results remain the main scientific analysis;
   secondary results summarize recurrence and do not replace them.

## 10. Data sources and reproducibility

### Scientific source documents

The figure design and wording should remain aligned with the repository KDA
design and validated KDA results explanation. These are internal implementation
sources and should not be cited or labeled in the public-facing figure.

### Production tables

Set `kda_input_dir` to the validated production KDA bundle. The
figure-generation code should validate and read:

```text
<kda_input_dir>/kda_status.tsv
<kda_input_dir>/kda_run_manifest.tsv
<kda_input_dir>/kda_checks.tsv
<kda_input_dir>/kda_artifacts.tsv
```

Use `kda_status.tsv` and the run manifest for production totals and
denominators. Do not derive planned, skipped, or no-result denominators from
`kda_results.tsv.gz`, because that file contains only significant returned
drivers.

If the example KDA result card is populated with a real result rather than
schematic placeholders, read it from:

```text
<kda_input_dir>/kda_results.tsv.gz
```

The script must require:

```text
validation_status = validated_complete
all validation checks passed
```

It should record all source paths and SHA-256 values in a figure manifest.

### Recommended implementation and outputs

Prefer a code-native vector graphic because the figure contains exact set
operations, mathematical notation, and many short labels. A suitable
implementation path is:

```text
scripts/figures/analysis/mitochondrial_kda/visualize_mitochondrial_kda_workflow.R
```

Recommended outputs:

```text
results/figures/analysis/mitochondrial_kda/
├── mitochondrial_kda_workflow.svg
├── mitochondrial_kda_workflow.pdf
├── mitochondrial_kda_workflow.png
├── mitochondrial_kda_workflow_plotted_data.tsv
├── mitochondrial_kda_workflow_manifest.tsv
└── mitochondrial_kda_workflow_checks.tsv
```

The SVG should be the editable master. Export the PNG at 300 dpi for review,
and retain the PDF for manuscript assembly.

The plotted-data table should store every displayed production count, its
source table and column, and whether it was read directly or derived. The
checks table should verify at minimum:

- 972 primary planned runs;
- 810 secondary planned runs;
- 1,782 total planned runs;
- planned equals eligible plus skipped plus failed;
- significant-run count does not exceed eligible-run count;
- every fine cell type maps to exactly one broad network;
- all three signature directions occur in both tiers; and
- the KDA production status is `validated_complete`.

## 11. Draft caption

> **Cell-type-specific mitochondrial key-driver analysis.** Validated
> AD-versus-NCI differential-expression calls were restricted using the
> validated `core_mito_protein` annotation and analyzed in the final
> directed Bayesian network assigned to each fine cell type. The primary
> analysis kept six sex/APOE strata separate and constructed AD-up, AD-down,
> and combined mitochondrial signatures, yielding 972 planned runs. The
> secondary analysis formed five prespecified sex- or APOE-level pools by
> taking set unions of member DEG calls; these are summaries of existing
> contrasts rather than newly fitted pooled contrasts and yielded 810 planned
> runs. For every run, the assigned broad network was induced on the exact
> tested genes (the intersection across source contrasts for a pool), and the
> effective query was the candidate mitochondrial signature intersected with
> that induced-network background. Runs with validated inputs, a nonempty
> induced network, and at least three effective query genes were eligible.
> NetWeaver tested directed downstream neighborhoods up to three layers with a
> one-sided hypergeometric test and applied Benjamini-Hochberg correction
> across candidate drivers within each run. Drivers with adjusted P values at
> or below 0.05 were reported as putative key drivers. Of 1,782 planned
> production runs, 1,021 were eligible, 840 returned at least one significant
> driver, 761 were skipped for prespecified eligibility reasons, and none
> failed. Network direction and enrichment support prioritization of candidate
> upstream regulators but do not establish causality, activation, or
> inhibition.

## 12. Review checklist before drawing

- [ ] Primary and secondary branches are equally easy to locate, but the
  primary branch is labeled as the main scientific analysis.
- [ ] All six primary groups and all five secondary pools are shown.
- [ ] Up, down, and exact-union signatures are shown for both tiers.
- [ ] Secondary query union and secondary background intersection are not
  confused.
- [ ] Direction-discordant pooled genes are represented accurately.
- [ ] Fine-cell-type signature scope and broad-network scope are distinct.
- [ ] The run-specific induced network and effective query intersection are
  visible.
- [ ] Eligibility is based on source status, network content, and query size,
  not statistical significance.
- [ ] Directed layers, hypergeometric enrichment, and within-run BH correction
  are labeled.
- [ ] Production counts use the run manifest/status denominators.
- [ ] Skipped, no-significant-result, and failed runs are visually distinct.
- [ ] The wording uses “putative key driver” or “candidate upstream
  regulator,” never proven causal regulator.
- [ ] The final caption contains the secondary-pool, FDR-scope, and causality
  caveats.
