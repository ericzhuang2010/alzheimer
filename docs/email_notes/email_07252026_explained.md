# Email 07/25/2026: second part explained

## Bottom line

The professor wants you to answer:

> Which upstream genes regulate the sex-, APOE-, and cell-type-specific mitochondrial changes seen in AD, and which of those genes are strong enough candidates for experimental perturbation?

This is not another ranking of mitochondrial DEGs. The main analysis should be a cell-type-specific network key-driver analysis (KDA), followed by integration with AD genetics and other evidence.

## What the second part contains

From the [email](email_07252026.txt), I interpret three deliverables:

1. Project your mitochondrial AD DEG signatures onto the matching cell-type Bayesian networks.
2. Find upstream network nodes whose downstream neighborhoods are significantly enriched for those DEGs.
3. Prioritize the resulting drivers using complementary evidence such as AD GWAS, cell-type QTLs, protein evidence, prior perturbations, and experimental tractability.

A crucial point: the key driver does not have to be mitochondrial or itself differentially expressed. A nuclear transcriptional regulator several steps upstream of many mitochondrial DEGs may be more interesting than a strongly changed respiratory-chain subunit.

Your existing [pre-network shortlist](../analysis/mt_pathway/pre_network_prioritization_report.md) should therefore be used as a benchmark and supporting evidence—not as the list of nodes allowed to become key drivers.

## What the Wang paper contributes

The [Wang paper](../wang_paper/wang_multiscale_modeling.pdf) follows this sequence:

```text
AD-associated molecular signature
              ↓
Bayesian causal network
              ↓
Find upstream nodes whose downstream neighborhoods contain
more signature genes than expected
              ↓
Key-driver candidates
              ↓
External evidence and experimental perturbation
```

The generalized KDA method searches multi-step downstream neighborhoods of every candidate node and tests enrichment for the target signature. A related Zhang-lab AD implementation used downstream neighborhoods from one through six steps, with `K = 6`. [Original KDA method](https://www.iaeng.org/publication/WCE2013/WCE2013_pp1309-1312.pdf), [AD KDA implementation](https://www.nature.com/articles/s41467-020-17405-z).

The local BN arrows mean putative upstream-to-downstream relationships. They do not indicate activation versus repression. Likewise, the edge weights appear to represent network support/stability, not positive or negative regulatory effects. Up- and downregulated DEG signatures can therefore be analyzed separately, but you cannot say that an edge is activating or inhibitory from these files.

Also, the Wang paper’s networks incorporated genotype/eQTL and TF priors. The provenance of your copied snRNA-seq BNs is less complete, so “putative key driver” is safer than “proven causal regulator.”

## Network file inventory and caveat

The final KDA should use each cell type’s `result.links3.links.txt`, not either combined table.

As rechecked on July 26, 2026, final de-looped network files are now present for all nine cell types:

| Cell-type network | Final edges | Nodes |
|---|---:|---:|
| [Astrocytes](../../bayesian_network/Astrocytes/result.links3.links.txt) | 8,881 | 8,285 |
| [CAMs](../../bayesian_network/CAMs/result.links3.links.txt) | 15,598 | 15,260 |
| [Excitatory neurons](../../bayesian_network/Excitatory_neurons/result.links3.links.txt) | 13,759 | 10,441 |
| [Inhibitory neurons](../../bayesian_network/Inhibitory_neurons/result.links3.links.txt) | 10,534 | 9,579 |
| [Microglia](../../bayesian_network/Microglia/result.links3.links.txt) | 6,826 | 6,604 |
| [OPCs](../../bayesian_network/OPCs/result.links3.links.txt) | 8,610 | 8,249 |
| [Oligodendrocytes](../../bayesian_network/Oligodendrocytes/result.links3.links.txt) | 9,067 | 8,190 |
| [T cells](../../bayesian_network/T_cells/result.links3.links.txt) | 10,481 | 10,360 |
| [Vasculature cells](../../bayesian_network/Vasculature_cells/result.links3.links.txt) | 5,266 | 5,290 |

All nine files are well formed, contain no duplicate edges, and pass a directed-acyclic-graph check. The separate [email-note Microglia copy](result.links3.links.txt) is byte-identical to the copy under `bayesian_network/Microglia`.

The root [BN_combined.all_edges.csv](../../bayesian_network/BN_combined.all_edges.csv) contains all nine cell types and weights, but it is pre-de-loop. For example, it contains both:

```text
FLRT2 → MIR99AHG
MIR99AHG → FLRT2
```

The final Vasculature `result.links3.links.txt` retains only the first direction. Similarly, the combined Microglia network has six edges removed from the final Microglia file.

The other combined file, [BN_combined.tsv](../../bayesian_network/BN_combined.tsv), also retains these cycles and collapses shared edges across cell types, sometimes averaging their weights. It should not be treated as the final cell-specific DAG.

The final edge lists are sufficient for topology-based KDA. For complete provenance and edge-support sensitivity analyses, it would still be useful to obtain these supporting files for every cell type:

```text
result.links3.links.txt   # final de-looped directed edges
result.links.3            # corresponding edges with support weights
bn.param.txt
prior.txt
bn.banned.txt
```

At present, these supporting construction and weighted-edge files are available locally only for Vasculature cells; the other eight directories contain only `result.links3.links.txt`. Their absence does not prevent an unweighted KDA, but it limits confirmation of network priors, construction parameters, and edge-support robustness.

The old [BN.KDA.summary_stats.csv](../../bayesian_network/BN.KDA.summary_stats.csv) cannot be reused: its DEG definitions and KDA parameters are undocumented and do not represent your six sex/APOE signatures.

## Recommended analysis

### 1. Construct the target signatures

For every selected fine cell type and sex/APOE stratum:

- Start with the Phase 08 AD-versus-NCI results.
- Define mitochondrial DEGs using the existing threshold: within-contrast BH FDR `< 0.05` and `|log2FC| > log2(1.3)`.
- Use prespecified MitoCarta and extended mitochondrial pathway membership.
- Create three queries: all mitochondrial DEGs, AD-up mitochondrial DEGs, and AD-down mitochondrial DEGs.
- Use all transcriptome-wide genes tested in that contrast and present in the network as the measurable universe—not only MitoCarta genes.
- Report how many query genes are represented in the network.

#### What is a KDA query?

A KDA query is the target gene set, or signature, given to the key-driver algorithm. It is not a database or search query.

Each KDA run needs:

```text
1. Query gene set: genes representing the biological response
2. Network: the matching cell-type Bayesian network
3. Background: measurable/tested genes represented in that network
4. Neighborhood range: for example, 1–6 downstream steps
```

##### What does the KDA background mean?

The background, or measurable universe, is the set of genes that had a fair
chance to become query genes and can also be evaluated in the network. For a
given cell-type/sex/APOE AD-versus-NCI comparison, use:

```text
KDA background
    = genes eligible for and tested in that exact MAST comparison
      ∩
      genes present as nodes in the matching cell-type Bayesian network
```

It is not all human genes, all MitoCarta genes, only the significant DEGs, or
automatically every node in the original network. Genes excluded from the
expression analysis or absent from the network could never occur in the
effective KDA query. Including them in the background would therefore distort
the expected overlap.

For example, suppose:

```text
10,000 genes were tested by MAST
 6,604 genes occur in the matching network
 5,500 genes occur in both sets
```

The KDA background is 5,500 genes. If a mitochondrial DEG query contains 60
genes but only 50 are in this background, the effective network query contains
50 genes. For a candidate driver's 100-gene downstream neighborhood, the
randomly expected overlap is approximately:

```text
100 × 50 / 5,500 = 0.91 query genes
```

If 10 query genes are actually observed downstream, KDA evaluates whether that
excess is statistically significant using the enrichment test.

The numbers above are illustrative, not the actual numbers for this dataset.
The background must be constructed separately for every comparison because
gene testability can differ among cell types and sex/APOE strata.

##### What is the expression filter before MAST?

In this project's Phase 08 pipeline, a gene is retained for MAST if it is
detected—that is, has nonzero expression—in at least 10% of the AD nuclei or at
least 10% of the NCI nuclei in that exact comparison. This is configured as
`min_pct: 0.10` in
[analysis_parameters.yml](../../config/analysis_parameters.yml) and passed to
Seurat `FindMarkers` as `min.pct` in
[08_run_mast.R](../../scripts/08_run_mast.R).

For example, with 500 AD nuclei and 400 NCI nuclei, a gene passes if it is
detected in at least 50 AD nuclei or at least 40 NCI nuclei:

```text
15% in AD and 2% in NCI  → passes
 3% in AD and 12% in NCI → passes
 8% in AD and 9% in NCI  → fails and is not tested
```

This filter removes genes that are too sparsely observed for a useful
comparison; it does not mean that the retained genes are differentially
expressed. There is no fold-change prefilter because `logfc_threshold` is zero.
Statistical significance and the final DEG effect-size threshold are applied
after testing.

##### Choices for the KDA query

The query should be selected to match the biological question. For this
project, the professor's question is specifically about upstream drivers of the
mitochondrial AD response, so the starting query should be:

```text
Biological query
    = AD-versus-NCI DEGs
      ∩ prespecified mitochondrial pathway genes

Effective KDA query
    = biological query
      ∩ nodes in the matching cell-type Bayesian network
```

Use the mitochondrial definition already established from MitoCarta and the
extended mitochondrial pathway annotations rather than choosing a pathway
after seeing which one gives the most attractive KDA results.

The main query choices are:

| Query choice | Question answered | Recommended role |
|---|---|---|
| All mitochondrial DEGs | What may drive the overall mitochondrial AD response? | Primary |
| AD-up mitochondrial DEGs | What may be upstream of mitochondrial genes increased in AD? | Primary |
| AD-down mitochondrial DEGs | What may be upstream of mitochondrial genes decreased in AD? | Primary |
| DEGs in a specific mitochondrial subpathway, such as oxidative phosphorylation, mitophagy, or mitochondrial translation | What may drive this narrower mitochondrial process? | Secondary, prespecified analysis |
| All transcriptome-wide DEGs | What may drive the complete AD transcriptional response in this cell type? | Separate, broader analysis |
| Phase 10 similarity-tail genes | What may organize a descriptive similarity pattern? | Exploratory; not a primary KDA query |

Narrow subpathway queries should be run only when enough DEG members are
represented in the matching network. Very small queries have weak and unstable
enrichment statistics, so report the original query size, the number mapped to
the network, and any minimum-size rule required by the lab's KDA
implementation.

Changing the query does not change the other KDA roles:

```text
Query genes
    = the selected mitochondrial DEG signature

Background
    = all genes tested in that exact MAST contrast
      ∩ matching network nodes

Candidate drivers
    = all eligible upstream nodes in the matching network
```

Do not restrict the background or the candidate drivers to mitochondrial genes.
A non-mitochondrial regulator can be a biologically important driver of a
mitochondrial expression program.

KDA then asks:

> Which upstream network nodes have downstream neighborhoods that are significantly enriched for genes in this query?

For example, consider:

```text
Cell type: Mic P2RY12
Stratum: Male APOE ε2
Comparison: AD versus NCI
```

Suppose its mitochondrial DEGs are:

| Gene | AD change |
|---|---|
| `TUFM` | Down |
| `TOMM7` | Down |
| `COX5B` | Down |
| `NDUFB7` | Down |
| `PPARGC1B` | Up |
| `SOD2` | Up |

Three separate KDA queries can be constructed.

**Query 1: all mitochondrial DEGs**

```text
TUFM
TOMM7
COX5B
NDUFB7
PPARGC1B
SOD2
```

This asks which upstream genes appear to regulate the overall mitochondrial AD response, regardless of expression direction.

**Query 2: AD-up mitochondrial DEGs**

```text
PPARGC1B
SOD2
```

This asks which upstream genes have an unusually large number of AD-increased mitochondrial genes downstream.

**Query 3: AD-down mitochondrial DEGs**

```text
TUFM
TOMM7
COX5B
NDUFB7
```

This asks which upstream genes have an unusually large number of AD-decreased mitochondrial genes downstream.

Each query produces its own key-driver results. Query genes and candidate drivers are different groups:

```text
Query genes
    = the mitochondrial DEGs the analysis is trying to explain

Candidate drivers
    = network nodes tested as possible upstream regulators
```

A candidate driver does not have to occur in the query. It can be non-mitochondrial and need not itself be a DEG. For example:

```text
Candidate regulator X
       ├──→ TUFM
       ├──→ TOMM7
       ├──→ COX5B
       └──→ NDUFB7
```

`Candidate regulator X` could become a key driver of the AD-down query even though it is absent from the query list.

The combined query usually contains more genes and may provide more statistical power, but it mixes increases and decreases. The direction-specific queries can reveal distinct programs:

```text
Driver A → genes elevated in AD
Driver B → genes reduced in AD
```

Because Bayesian-network edges are not signed, this separation does not prove that Driver A activates genes or Driver B represses them. It only identifies which expression-direction signature is concentrated downstream.

In short:

> A KDA query is the gene program the network is being asked to explain. Here, each query is a particular collection of mitochondrial AD DEGs from one cell type and one sex/APOE group.

Do not use the Phase 10 bottom-200 similarity tails as the primary KDA queries. They are descriptive, comprise roughly 27–29% of the mitochondrial universe, and contain no gene-level FDR discoveries.

Because testing all 321 estimable contrasts would create a large multiplicity problem, predefine a primary panel based on Part 1—for example the most informative superficial/RELN-positive excitatory populations, `Ast GRM3`, `Mic P2RY12`, and OPCs. Run the full set as secondary discovery analysis.

### 2. Run KDA

For each signature and matching network:

1. Restrict the network to measurable genes.
2. Let every eligible network node be a potential driver.
3. Search its one- through six-step downstream neighborhoods using the Wang KDA implementation.
4. Test whether each neighborhood contains more query genes than expected.
5. Apply BH correction within each signature; also calculate a global correction across signatures as a sensitivity analysis.
6. Retain the neighborhood size, overlap genes, enrichment, raw P value, adjusted P value, and network support.

#### Wang KDA code availability

The KDA implementation used for the Wang paper is publicly available in the
[Wang `proteomics_networks` repository](https://github.com/wange230/proteomics_networks).
The relevant upstream directory contains the packaged KDA implementation,
`KDA-0.2.tar.gz`, the main `PHG_Proteomics_global_KDA.R` script, and supporting
downstream-neighborhood and enrichment scripts. A provenance-preserving local
copy has been downloaded to
[`bayesian_network/wang_kda_code`](../../bayesian_network/wang_kda_code/SOURCE.md).

The main Wang Bayesian-network script specifies:

```text
directed = TRUE
nlayers = 6
FET_pvalue_cut = 0.05
boost_hubs = TRUE
dynamic_search = TRUE
bonferroni_correction = TRUE
```

There is a version-label discrepancy that should be confirmed with the lab:
the paper describes KDA version `0.02`, whereas the public archive is named
`KDA-0.2.tar.gz` and its internal `DESCRIPTION` reports version `0.2`. This may
be a typographical difference, but exact reproducibility should not assume so
without confirmation.

Use Wang's public package and scripts as the primary implementation rather than
substituting KDA code from another paper. The scripts are not directly
turnkey for this project: they contain hard-coded paths and were written for
the PHG proteomic network. Adapt their inputs to the cell-type-specific
transcriptomic networks, mitochondrial DEG queries, and contrast-specific
backgrounds described above. Ask the lab to confirm the version discrepancy
and any run-specific preprocessing or parameters not documented in the public
repository. An independently implemented Fisher/hypergeometric test remains
useful as a validation audit.

Useful controls include degree-matched random signatures, alternate DEG thresholds, up/down/combined signatures, different maximum path lengths, and related fine-cell subtypes mapped to the same broad network.

### 3. Require robustness

A convincing candidate should ideally satisfy several of these:

- significant KDA in the biologically matching cell type;
- recovered in a related fine subtype or another sex/APOE signature with a coherent pattern;
- stable across neighborhood depths and DEG thresholds;
- supported by a coexpression network, if the matching MEGENA networks can be obtained;
- supported by local regulator evidence or prior perturbation evidence;
- not driven by one enormous generic network neighborhood.

For now, the Microglia male-ε2 signature provides a good pipeline pilot: it has 88 unique core-mito DEGs, 87 of which occur in the combined Microglia network. Vasculature signatures are much smaller and are less useful for the first test.

### 4. Add complementary evidence

For each significant KD, create separate evidence columns rather than one opaque score:

- AD GWAS fine-mapped gene or credible-set support;
- cell-type eQTL/sQTL–GWAS colocalization or TWAS support;
- cell-type chromatin/caQTL evidence;
- replication in independent AD proteomics or transcriptomics;
- TF/regulon evidence;
- existing CRISPR, knockdown, or overexpression effects;
- essentiality, dosage tolerance, subcellular localization, and experimental tractability.

The current FunGen-AD resource provides harmonized AD GWAS and fine-mapping outputs, while large ROSMAP single-nucleus studies provide cell- and subtype-specific eQTLs. [FunGen-AD GWAS](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/gwas/AD_GWAS/), [ROSMAP cell-subtype eQTL study](https://www.nature.com/articles/s41588-024-01685-y), [FunGen-AD caQTL/colocalization](https://adsp-fgc.niagads.org/xqtl-resources/xqtl-data/qtl/caQTL/).

GWAS support should increase confidence, not serve as a mandatory filter: a trans-acting network driver may not reside in an AD GWAS locus.

## Expected final output

The useful deliverable to the professor would be:

- a table of every KDA result by cell type, stratum, direction, and neighborhood depth;
- a concise top-driver table with network, local, genetic, external, and experimental evidence;
- three to five driver-centered network figures;
- sensitivity and negative-control results;
- a final panel of approximately 5–10 perturbation candidates plus downstream mitochondrial readouts.

`ATP5IF1`, `TUFM`, `TOMM7`, `PPARGC1B`, `PPARGC1A`, and `SMARCD3` remain sensible pre-network candidates. But the KDA should be permitted to discover entirely different upstream genes.

A concise message to the professor could be:

> I understand the goal as projecting the sex/APOE- and cell-type-specific mitochondrial DEG signatures onto the matching ROSMAP Bayesian networks, running downstream-neighborhood KDA, and then integrating the resulting drivers with AD genetics and perturbation evidence. I will initially analyze up-, down-, and combined mitochondrial DEG signatures separately using the public Wang KDA package and scripts. Could you confirm whether the paper's KDA `0.02` corresponds to the repository's `0.2` package, whether the six-layer directed settings should be retained, and whether there were any additional preprocessing or background-universe rules not documented in the public repository?
## Plain-language explanation of cell-type-specific KDA


“Cell-type-specific network key-driver analysis” means finding genes that may sit upstream of a disease-related gene program within a particular brain cell type.

The phrase has four parts:

- **Cell-type-specific:** Analyze separate networks for microglia, astrocytes, excitatory neurons, and other cell types. A gene can be a driver in microglia but not in neurons.
- **Network:** Genes are connected by directed relationships such as `A → B`, meaning A is predicted to be upstream of B.
- **Key driver:** A gene whose downstream network neighborhood contains unusually many genes from the biological signature of interest.
- **Analysis:** Statistically test every eligible upstream gene and correct for testing many candidates.

For this project, the signature of interest is a set of mitochondrial genes that differ between AD and NCI in a particular sex/APOE group:

```text
Male-ε2 microglial mitochondrial DEGs
                    ↓
       Microglia Bayesian network
                    ↓
For each possible upstream gene:
collect its downstream genes 1–6 steps away
                    ↓
Test whether mitochondrial DEGs are unusually concentrated there
                    ↓
        Significant key drivers
```

For example, suppose the male-ε2 `Mic P2RY12` signature contains:

```text
TUFM, TOMM7, COX5B, NDUFB7, ATP5IF1
```

Imagine that the Microglia network contains:

```text
REGULATOR_X → TUFM
REGULATOR_X → GENE_Y → TOMM7
REGULATOR_X → GENE_Z → COX5B
REGULATOR_X → GENE_W → NDUFB7
```

Four of the five mitochondrial DEGs occur downstream of `REGULATOR_X`. If that concentration is much greater than expected by chance, `REGULATOR_X` becomes a candidate Microglia key driver for the male-ε2 mitochondrial response.

This is only an illustrative example; `REGULATOR_X` and these paths were invented to explain the method.

Important distinctions are:

- A key driver need not be a mitochondrial gene or a DEG.
- It is not merely the gene with the most connections. Its neighborhood must be specifically enriched for the mitochondrial DEG set.
- The same gene may be a driver in one cell type or sex/APOE stratum but not another.
- The arrow indicates predicted upstream direction, not activation or repression.
- A significant result is a putative regulator, not proof of causality.

In one sentence, the analysis asks:

> Within each brain-cell regulatory network, which upstream genes appear to control an unexpectedly large portion of the mitochondrial AD response seen in each sex/APOE group?

## How a predicted network path is obtained

For a real path such as:

```text
REGULATOR_X → GENE_Y → TOMM7
```

the final cell-type network file would contain two rows:

```text
REGULATOR_X    GENE_Y
GENE_Y         TOMM7
```

Because each row is interpreted as `source → target`, graph traversal produces the two-step path from `REGULATOR_X` to `TOMM7`. However, the Bayesian network predicts this relationship; it does not demonstrate it experimentally.

### How the arrows were inferred

The previous lab member’s pipeline approximately did the following:

1. Measured gene expression across many nuclei of a particular cell type.
2. Discretized each gene’s expression into low, medium, and high states.
3. Used RIMBANet to search for directed network structures that explain the observed joint expression patterns.
4. Repeated the network search many times. The Vasculature configuration indicates 1,000 network runs.
5. Retained repeatedly observed edges to construct a consensus network.
6. Removed weak edges involved in cycles to produce the final directed acyclic network in `result.links3.links.txt`.

An edge’s weight in `result.links.3` likely represents how frequently that edge appeared across the sampled networks. For example:

```text
REGULATOR_X → GENE_Y    weight = 0.82
```

would ordinarily mean that the edge occurred in approximately 82% of the sampled networks. This interpretation should be confirmed from the original construction script or with the previous analyst.

An inferred edge means that, given the data and network assumptions, placing the source gene upstream of the target helped explain their conditional dependence. It does not necessarily mean direct promoter binding, activation, repression, or experimentally proven causality. There may be omitted intermediate biology, hidden confounding, or another direction that explains the expression data nearly as well.

Expression data alone are often insufficient to determine direction uniquely. Direction becomes more credible when the network uses external anchors such as eQTLs, genotype-based causal inference, known TF-target relationships, chromatin evidence, and replication across independent datasets.

The Wang paper used matched genetic data, eQTL-based causal inference, and ENCODE TF-target priors. For the copied snRNA-seq networks, the available companion code confirms expression discretization and RIMBANet, but the construction parameters reference a missing `prior.txt`. It is therefore not yet clear how much genetic or TF-prior information contributed to their directions.

The appropriate wording is:

> The cell-type Bayesian network predicts `REGULATOR_X` to be upstream of `GENE_Y`, which is predicted to be upstream of `TOMM7`.

Perturbing `REGULATOR_X` and then measuring `GENE_Y`, `TOMM7`, and the mitochondrial phenotype would provide much stronger evidence for the proposed chain.

## What the Bayesian network is used for

A Bayesian network predicts directional gene-to-gene dependencies:

```text
Gene A → Gene B
```

This suggests that Gene A is upstream of Gene B in the statistical network. Gene A does not have to be a known transcription factor, and the edge does not necessarily represent direct molecular regulation.

A DEG analysis tells us what changed:

```text
TOMM7 is lower in male-ε2 AD
COX5B is lower in male-ε2 AD
NDUFB7 is lower in male-ε2 AD
```

It does not tell us why those genes changed or which gene should be perturbed. The Bayesian network organizes genes into possible upstream and downstream relationships:

```text
Candidate regulator
       ↓
Intermediate genes
       ↓
TOMM7, COX5B, NDUFB7 and other mitochondrial DEGs
```

KDA then asks whether one upstream gene has significantly more mitochondrial AD DEGs downstream than expected by chance. That upstream gene becomes a candidate experimental target.

The Bayesian network can predict:

- one gene as statistically upstream of another;
- multi-step paths between genes;
- upstream hubs affecting many downstream genes;
- different regulatory structures in different cell types; and
- candidate regulators that are not themselves DEGs.

It does not directly predict whether the effect is positive or negative. `A → B` does not distinguish `A activates B` from `A represses B`, and the network does not prove direct binding or causality.

Correlation or coexpression provides an undirected relationship, `Gene A — Gene B`: the genes vary together, but there is no proposed upstream candidate. A Bayesian network attempts to assign direction, `Gene A → Gene B`, making it possible to search for genes upstream of the mitochondrial response.

The practical division of labor is:

> DEG analysis identifies the mitochondrial phenotype; the Bayesian network proposes upstream regulatory structure; KDA identifies which upstream genes are the strongest candidate controllers of that phenotype.

Those candidates must then be checked using genetics, TF/chromatin evidence, independent datasets, and ultimately perturbation experiments.
