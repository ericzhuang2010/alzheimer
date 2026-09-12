# RPL11 in astrocytes: actionable STRING analysis plan

## Purpose

Use STRING to test whether the protein encoded by the Phase 18 key-driver candidate **RPL11** has independent protein-network support with the genes implicated by the three supporting astrocyte KDA runs.

This is a cross-validation analysis, not a rerun of KDA. The central question is:

> Do RPL11 and its run-specific KDA-associated genes show more experimentally supported or curated protein connectivity than expected by chance?

The primary analysis should use **RPL11 plus the exact target genes from each supporting run**. Do not start by uploading every astrocyte DEG or every gene in the full KDA neighborhood. A large mixed list would mainly show that mitochondrial proteins interact with one another and would not specifically validate RPL11.

STRING can support a protein-level relationship, a functionally coherent module, or plausible intermediate proteins. It cannot by itself establish that RPL11 regulates these genes, prove an edge direction, or demonstrate that an association occurs specifically in astrocytes or Alzheimer disease.

## Existing Phase 18 evidence to be tested

RPL11 is the rank-1 non-mitochondrial driver candidate in the current Phase 18 results. Its aggregate evidence is strong, but it is concentrated in three conservative-support astrocyte runs:

- eligible runs: 21
- usable runs: 20
- conservative-support runs: 3
- supporting fine cell types: 2 (`Ast CHI3L1` and `Ast GRM3`)
- supporting groups: 3 (`M_e4`, `M_e2`, and `F_e2`)
- aggregate ACAT p-value: `1.78 × 10^-8`
- aggregate FDR: `3.44 × 10^-5`
- candidate stability under leave-one-group-out analysis: 2 of 3 assessable repetitions

This makes RPL11 appropriate for targeted protein-network validation, while also making matched-null tests important.

## Analysis design

Run the analyses in the order below. The first three run-specific networks are the primary tests. The consensus networks are summaries and sensitivity analyses.

### 1. Primary run-specific input sets

| Run | Astrocyte context | KDA result | STRING input |
|---|---|---:|---|
| `primary_Ast_CHI3L1_M_e4_AD_down_mito` | Ast CHI3L1, male, APOE ε4, AD-down | layer 2; overlap 3; fold enrichment 30.72; q = 0.0167 | `RPL11`, `COX7C`, `PSAP`, `TOMM7` |
| `primary_Ast_GRM3_M_e2_AD_down_mito` | Ast GRM3, male, APOE ε2, AD-down | layer 3; overlap 11; fold enrichment 12.13; q = 1.90 × 10^-7 | `RPL11`, `NDUFB4`, `COX7C`, `UQCRB`, `PSAP`, `ATP5F1E`, `ATP5PF`, `SLIRP`, `CYB5R3`, `UQCRH`, `ATP5ME`, `COX6C` |
| `primary_Ast_GRM3_F_e2_AD_up_mito` | Ast GRM3, female, APOE ε2, AD-up | layer 2; overlap 6; fold enrichment 33.52; q = 7.15 × 10^-6 | `RPL11`, `COX7C`, `PSAP`, `NDUFB4`, `TOMM7`, `UQCRB`, `ATP5PF` |

Analyze the runs separately because they differ in astrocyte subtype, sex/APOE group, direction of differential expression, and KDA layer. Combining them first would hide this heterogeneity.

### 2. Strict recurrent consensus set

Use RPL11 plus targets present in at least two of the three support runs:

```text
RPL11
COX7C
PSAP
ATP5PF
NDUFB4
TOMM7
UQCRB
```

Target recurrence is:

- 3 of 3 runs: `COX7C`, `PSAP`
- 2 of 3 runs: `ATP5PF`, `NDUFB4`, `TOMM7`, `UQCRB`

This is the cleanest small consensus network and should be the main consensus figure.

### 3. Full target-union sensitivity set

Use RPL11 plus every target found in at least one support run:

```text
RPL11
COX7C
PSAP
ATP5PF
NDUFB4
TOMM7
UQCRB
ATP5F1E
ATP5ME
COX6C
CYB5R3
SLIRP
UQCRH
```

The six targets unique to the 11-target Ast GRM3 male ε2 run are `ATP5F1E`, `ATP5ME`, `COX6C`, `CYB5R3`, `SLIRP`, and `UQCRH`.

### 4. Do not use these as the primary input

Do not use the following for the main validation test:

- all astrocyte DEGs;
- the entire three-layer KDA neighborhood;
- the 18-node displayed Bayesian consensus network;
- extra STRING interactors added before testing the submitted proteins.

Those inputs answer broader exploratory questions and create strong size, degree, and pathway biases. They can be used only after the prespecified analysis is complete.

The current Bayesian consensus network contains directed KDA edges such as `RPS25 → RPLP1 → RPL11` and direct outgoing edges `RPL11 → COX7C`, `RPL11 → CWC15`, and `RPL11 → PRDX1`. These are useful for a secondary KDA-versus-STRING overlay, but only `COX7C` is one of the run-specific mitochondrial query hits directly linked to RPL11 in that Bayesian graph. Do not treat all displayed connector genes as independent target evidence.

## Step-by-step STRING web analysis

Use the STRING multiple-proteins search at <https://string-db.org/>.

Repeat the following workflow for each of the three run-specific sets, the recurrent consensus set, and the full union set.

### Step 1: Map the proteins

1. Select **Multiple proteins**.
2. Paste one gene symbol per line.
3. Select **Homo sapiens**.
4. Confirm every symbol maps to the intended human protein.
5. Export or screenshot the mapping table and record any unmapped or ambiguous symbol.

Do not silently discard an unmapped gene. Report the number submitted, number mapped, and final denominator for every result.

### Step 2: Build the strict physical network

Use these settings first:

- network type: **physical subnetwork**;
- minimum required interaction score: **high confidence, 0.700**;
- first shell of interactors: **0**;
- second shell of interactors: **0**;
- network display: evidence view for inspection, then confidence view for the figure;
- organism: **Homo sapiens**.

This is the primary protein-network test. It asks whether submitted proteins have evidence consistent with a physical protein association without allowing STRING to make the network look connected by inserting additional proteins.

Export:

- the interaction table in TSV format;
- the network as SVG;
- a screenshot or settings record;
- the STRING version and access date.

### Step 3: Identify RPL11-to-target edges

For every edge incident on RPL11, record:

- target protein;
- combined STRING score;
- experimental evidence score;
- curated-database evidence score;
- other supporting evidence channels;
- whether the edge passes the 0.700 threshold;
- whether the edge appears in one, two, or all three run-specific analyses.

The strongest cross-validation result is a direct RPL11–target edge supported by **experiments and/or curated databases**. A combined score driven only by text mining is weak supporting evidence and should not be described as a validated interaction.

### Step 4: Build the functional association network

Repeat the same analysis using the **full/functional STRING network**, still with:

- required score 0.700;
- zero additional interactors.

Keep this result separate from the physical network. Functional association means that proteins participate in related biological processes; it does not necessarily mean that they bind one another.

### Step 5: Run confidence-threshold sensitivity checks

Repeat the input-only physical network at:

- medium confidence: 0.400;
- high confidence: 0.700, the primary threshold;
- highest confidence: 0.900.

A claim is more convincing if the key RPL11 edge remains at 0.900 and contains experimental or curated-database evidence. An edge found only at 0.400 should be described as suggestive.

### Step 6: Inspect network enrichment

Record the PPI-enrichment result for each input set:

- number of mapped proteins;
- observed edges;
- expected edges;
- average node degree;
- clustering coefficient, if supplied;
- PPI-enrichment p-value.

Interpret this carefully. The target list contains multiple oxidative-phosphorylation proteins, which are already expected to interact. A significant PPI-enrichment p-value may therefore show that the **mitochondrial targets form a coherent module**, not that RPL11 connects to that module.

Always report two quantities separately:

1. connectivity among all submitted proteins; and
2. connectivity specifically between RPL11 and the submitted targets.

### Step 7: Run STRING functional enrichment

Export enrichment results for at least:

- Gene Ontology Biological Process;
- Gene Ontology Cellular Component;
- Reactome pathways;
- KEGG pathways, if returned;
- STRING local network clusters.

Use the project-specific tested-gene universe as the statistical background when supported. The appropriate universe is the set of genes that could have entered the Phase 18 astrocyte KDA/mitochondrial overlap analysis after all expression and eligibility filters—not all human genes.

Keep only terms passing Benjamini–Hochberg FDR < 0.05 for confirmatory reporting. Report term ID, term name, observed gene count, background count, effect/enrichment strength, raw p-value, FDR, and member genes. Collapse redundant terms before making a figure.

The existing Phase 18 analysis already found electron-transport/oxidative-phosphorylation and cristae-related signals. STRING enrichment is useful as an independent database check, but it is not independent evidence if the same gene list mechanically generates the same pathway result. The protein-edge analysis is more informative for the RPL11 question.

### Step 8: Add candidate connector proteins only as exploration

After completing the zero-interactor analysis, allow at most five first-shell interactors in a separate exploratory network.

For each added protein, ask:

- Does it connect RPL11 to at least one mitochondrial target?
- Is each step supported by experiments or curated databases?
- Is the connector expressed in the project astrocytes?
- Is it already present in the Bayesian KDA network?
- Does the path remain at a 0.700 or 0.900 threshold?

An added connector generates a mechanism hypothesis. It is not part of the prespecified cross-validation result and should be drawn with a distinct shape or border.

## How to interpret STRING's seven evidence channels

STRING combines seven types of evidence. Record the channel-level evidence rather than reporting only the combined score.

| STRING channel | What it means | Use for RPL11 analysis | Reporting strength |
|---|---|---|---|
| Experiments | Evidence from laboratory interaction assays aggregated by STRING. Assays differ in whether they demonstrate direct binding, complex membership, or proximity. | Strongest channel for a proposed RPL11 protein relationship. Check the underlying publication and assay before calling it direct binding. | Strong when the primary paper and assay support the claim. |
| Curated databases | Protein complexes or pathway relationships curated by expert databases. | Strong support for established complex membership or a known pathway relationship. Inspect which database supplied the edge. | Strong for established association; not automatically astrocyte- or AD-specific. |
| Co-expression | Genes show correlated expression across datasets or conditions. | Supports functional coordination but may reflect cell composition, stress, or shared regulation. It is not a physical interaction. | Moderate functional evidence; weaker for a protein-binding claim. |
| Genomic neighborhood | Orthologous genes occur near one another across genomes. This evidence is most informative in prokaryotes. | Usually limited for a human RPL11–mitochondrial target claim; it can reflect conserved microbial operon organization rather than a human physical interaction. | Contextual only. |
| Gene fusion | Separate proteins in one species occur as a fused protein in another species. | Can suggest evolutionary functional linkage, but does not demonstrate a human astrocyte interaction. | Contextual mechanistic evidence. |
| Gene co-occurrence | Genes have correlated presence or absence across species. | Can support membership in an evolutionarily conserved process. It is vulnerable to broad phylogenetic and organelle-related patterns. | Contextual; not direct protein evidence. |
| Text mining | Protein names co-occur in scientific abstracts or other curated text sources. | Useful for finding literature, but it may reflect repeated discussion rather than experimental evidence. Follow the references manually. | Weak alone; never label an edge validated from text mining only. |

Evidence channels are not guaranteed to be statistically independent. The combined STRING score should therefore be treated as a confidence summary, not as a new experimental p-value.

## Publication-grade matched-null analysis

A visually connected STRING network is not sufficient for publication. Test whether RPL11 performs better than appropriate controls using the same settings and metrics.

### Null test A: replace RPL11, keep the targets fixed

For each control protein, submit:

```text
control protein + the same target set
```

Use the same species, physical-network definition, score threshold, and zero-interactor rule. Run this separately for the recurrent consensus targets and the full target union.

The existing file `results/figures/analysis/phase_18_key_driver_selection/RPL11/phase18_rpl11_matched_controls.tsv` provides two useful starting control groups:

- Phase 18 topology-plus-expression matched proteins;
- cytosolic ribosomal comparison proteins.

The existing matching audit reports residual imbalance, so do not claim that these controls are perfectly matched. For the STRING test, additionally match or stratify on:

- total STRING degree or connectivity;
- whether the control maps to STRING;
- protein abundance/detectability when available;
- astrocyte expression;
- KDA in-degree and out-degree;
- ribosomal-protein status.

The ribosomal controls answer an important specificity question: is RPL11 unusually connected to the target module, or would many cytosolic ribosomal proteins produce the same result?

### Null test B: keep RPL11, replace the target set

Randomly sample target sets of the same size from the genes eligible for the original astrocyte mitochondrial KDA analysis. Match random targets to the observed targets on:

- astrocyte expression;
- mitochondrial annotation class;
- STRING mapping status;
- STRING degree;
- protein detectability, if available.

Use at least 1,000 random target sets for the publication analysis. This tests whether RPL11 is unusually connected to these particular mitochondrial targets rather than to arbitrary well-studied mitochondrial proteins.

### Prespecified primary statistics

For every real and null network, calculate:

1. number of direct RPL11-to-target physical edges at score ≥ 0.700;
2. proportion of mapped targets directly connected to RPL11;
3. number of direct RPL11-to-target edges with nonzero experimental and/or curated-database evidence;
4. maximum and mean RPL11-to-target combined score;
5. observed-minus-expected edge count for the complete submitted network;
6. PPI-enrichment p-value for the complete submitted network.

The primary endpoint should be item 3: the number of direct RPL11-to-target edges with experimental and/or curated-database support. This focuses the test on protein evidence relevant to RPL11 and reduces the risk that dense target-to-target mitochondrial interactions dominate the result.

Calculate an empirical p-value as:

```text
p_empirical = (1 + number of null statistics >= observed statistic) / (B + 1)
```

where `B` is the number of matched controls or random target sets. Also report the observed effect, null median, null interquartile range, and empirical percentile. Apply FDR correction across the three run-specific confirmatory tests if they are tested separately.

## Reproducible STRING API workflow

The web workflow is good for inspection. Use the STRING API for final tables, matched-null analyses, and reproducibility. In this repository, make STRING requests through:

```text
.agents/skills/string-skill/scripts/rest_request.py
```

Use:

- base URL: `https://string-db.org/api/json`;
- species taxon: `9606`;
- a stable caller identity such as `alzheimer_phase18_rpl11`;
- POST requests for gene lists;
- newline-separated identifiers encoded as `%0d`;
- a small preview (`limit=10`, `max_items=10`) before saving the complete raw response.

### Example: strict recurrent physical network

```bash
echo '{
  "base_url": "https://string-db.org/api/json",
  "path": "network",
  "method": "POST",
  "form_body": {
    "identifiers": "RPL11%0dCOX7C%0dPSAP%0dATP5PF%0dNDUFB4%0dTOMM7%0dUQCRB",
    "species": 9606,
    "network_type": "physical",
    "required_score": 700,
    "add_nodes": 0,
    "limit": 10,
    "caller_identity": "alzheimer_phase18_rpl11"
  },
  "max_items": 10
}' | python .agents/skills/string-skill/scripts/rest_request.py
```

The preview is a mapping/settings check, not the final export. For the final run, save the complete raw response and retain the exact request parameters in a manifest. Repeat with the full/functional network and with required scores of 400 and 900.

### Example: full target-union physical network

Use this identifier string:

```text
RPL11%0dCOX7C%0dPSAP%0dATP5PF%0dNDUFB4%0dTOMM7%0dUQCRB%0dATP5F1E%0dATP5ME%0dCOX6C%0dCYB5R3%0dSLIRP%0dUQCRH
```

### API endpoints to use

| Endpoint | Purpose | Analysis role |
|---|---|---|
| `network` | Return edges among submitted proteins under specified network settings. | Primary edge table. |
| `interaction_partners` | Find possible proteins associated with RPL11. Start with `limit=10`. | Exploratory connector search only. |
| `enrichment` | Return GO/pathway/domain enrichment for the submitted proteins. | Secondary functional coherence analysis. |
| `ppi_enrichment` | Test whether the submitted proteins have more edges than expected. | Whole-list network-density summary. |

Save every raw response, then build cleaned tables without overwriting the raw data. Record the API access date because STRING content and scores can change between releases.

## Required output files

Create a dedicated results directory, for example:

```text
results/validation/phase18_string/rpl11_astrocytes/
```

The final package should contain:

| File | Required content |
|---|---|
| `rpl11_astro_string_input_sets.tsv` | run ID, context, input-set type, gene symbol, recurrence, KDA layer, and DEG direction |
| `rpl11_astro_string_mapping.tsv` | submitted symbol, mapped STRING ID, preferred name, mapping status, species |
| `rpl11_astro_string_physical_edges.tsv` | run/set, node A, node B, combined score, seven evidence-channel scores, threshold |
| `rpl11_astro_string_functional_edges.tsv` | equivalent table for the functional network |
| `rpl11_astro_string_ppi_summary.tsv` | mapped nodes, observed/expected edges, degree, clustering, PPI p-value |
| `rpl11_astro_string_enrichment.tsv` | database, term ID/name, gene counts, strength/effect, p-value, FDR, member genes |
| `rpl11_astro_string_matched_null.tsv` | control ID or replicate, matching variables, test statistic, empirical comparison |
| `rpl11_astro_string_request_manifest.tsv` | STRING version/date, endpoint, species, input hash, score threshold, network type, added-node count |
| `rpl11_astro_string_evidence_summary.md` | concise interpretation of direct, indirect, and absent support |
| `rpl11_astro_string_network.svg` | publication-ready consensus figure |

## Publication figure

Make a two-panel figure:

- **Panel A:** the directed astrocyte KDA consensus network, preserving arrow direction;
- **Panel B:** the STRING physical network for the strict recurrent input set, using undirected edges.

Recommended encoding:

- RPL11: large diamond;
- recurrent targets: circles, with a darker fill for 3-of-3 recurrence;
- one-run targets, if the union network is shown: lighter circles;
- STRING experimental/database edges: solid lines;
- other functional-only edges: dashed lines in a separate supplementary panel;
- connector proteins added by STRING: gray outlined nodes;
- edge width: STRING combined confidence.

Do not draw STRING edges with arrows. Do not merge KDA posterior edge strength and STRING confidence into one number. The two networks represent different evidence types.

## Decision rules for the RPL11 claim

### Strong protein-network support

Use this conclusion only if:

- RPL11 has one or more direct edges to prespecified targets in the input-only physical network;
- the edge is supported by experiments and/or curated databases;
- it survives the 0.700 threshold, preferably 0.900;
- RPL11 exceeds matched ribosomal and topology/expression controls;
- the result is not driven only by target-to-target mitochondrial interactions.

Appropriate wording:

> STRING provided independent protein-network support for an association between RPL11 and the astrocyte KDA target module, including [specific edges/evidence], with greater connectivity than matched controls.

### Module support without direct RPL11 support

Use this conclusion if the mitochondrial targets have significant PPI enrichment but RPL11 has no direct experimentally or database-supported target edge.

Appropriate wording:

> STRING supported protein-level coherence of the mitochondrial target module but did not provide direct protein-interaction support linking RPL11 to that module.

### Functional-only or connector-mediated support

Use this if RPL11 connects only in the functional network or only after adding proteins.

Appropriate wording:

> STRING suggested an indirect functional path between RPL11 and the mitochondrial module; this path is hypothesis-generating and requires independent validation.

### Little or no STRING support

No STRING edge does not invalidate the KDA result. STRING is incomplete, biased toward studied proteins, not astrocyte-specific, and unable to represent many transcriptional or stress-response mechanisms. In that case, report the negative result and prioritize orthogonal validation such as astrocyte proteomics, perturbation, co-immunoprecipitation/proximity assays, or independent cohort replication.

## Immediate execution checklist

1. Freeze the three run-specific input lists above in `rpl11_astro_string_input_sets.tsv`.
2. Run and export the three input-only physical networks at score 0.700.
3. Record every direct RPL11 edge and its seven evidence channels.
4. Run the recurrent consensus and full-union networks.
5. Repeat with functional networks and 0.400/0.900 sensitivity thresholds.
6. Export PPI and functional-enrichment results using the eligible astrocyte analysis universe as background.
7. Run driver-replacement controls, especially the ribosomal controls.
8. Run at least 1,000 matched target-set permutations.
9. Create the paired KDA/STRING figure and a complete request manifest.
10. Base the paper claim on direct RPL11 evidence and matched-null results—not on the visual density of the mitochondrial target subnetwork.

## Local source files

- `results/figures/analysis/phase_18_key_driver_selection/RPL11/phase18_rpl11_run_annotations.tsv`
- `results/figures/analysis/phase_18_key_driver_selection/RPL11/phase18_rpl11_run_target_matrix.tsv`
- `results/figures/analysis/phase_18_key_driver_selection/RPL11/astrocyte/phase18_rpl11_astrocyte_consensus_network_nodes.tsv`
- `results/figures/analysis/phase_18_key_driver_selection/RPL11/astrocyte/phase18_rpl11_astrocyte_consensus_network_edges.tsv`
- `results/figures/analysis/phase_18_key_driver_selection/RPL11/astrocyte/phase18_rpl11_astrocyte.graphml`
- `results/figures/analysis/phase_18_key_driver_selection/RPL11/phase18_rpl11_matched_controls.tsv`
- `results/figures/analysis/phase_18_key_driver_selection/RPL11/phase18_rpl11_matching_balance.tsv`
- `results/figures/analysis/phase_18_key_driver_selection/RPL11/phase18_rpl11_matched_null_results.tsv`

## STRING references

- STRING homepage and web interface: <https://string-db.org/>
- STRING API documentation: <https://string-db.org/help/api/>
- STRING evidence-channel description: <https://string-db.org/cgi/help?sessionId=bOVsCB5rNNsJ&subpage=evidence>
