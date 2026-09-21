#!/usr/bin/env node

/** Standardize mitochondrial gene-set terminology after the definitions on slides 6 and 7. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const SKILL_DIR =
  "/Users/rzhuang/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations";
const WORKSPACE_DIR = "/Users/rzhuang/Documents/VscodeProjects/alzheimer";
const SOURCE = path.join(
  WORKSPACE_DIR,
  "docs/presentations/09162026/09162026_sex_apoe_kda_fine_broad.pptx",
);
const BUILD_DIR = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_mito_gene_set_terms_20260920/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_mito_gene_set_terms_20260920/output/09162026_sex_apoe_kda_fine_broad_mito_gene_set_terms_20260920.pptx",
);
const EXPECTED_SLIDES = 160;
const CHART_SLIDE = 14;
const CHART_SERIES_NAMES = [
  "Core MT genes (13)",
  "Nuclear-encoded OXPHOS genes (86)",
];
const OLD_CHART_SERIES_NAMES = [
  "13 OXPHOS genes encoded by mitochondrial DNA",
  "86 structural OXPHOS genes encoded by nuclear DNA",
];

function slidesFromPresentation(presentation) {
  if (Array.isArray(presentation.slides?.items)) return presentation.slides.items;
  if (
    Number.isInteger(presentation.slides?.count) &&
    typeof presentation.slides.getItem === "function"
  ) {
    return Array.from(
      { length: presentation.slides.count },
      (_, index) => presentation.slides.getItem(index),
    );
  }
  throw new Error("Could not enumerate presentation slides");
}

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

async function blobBuffer(blob) {
  return Buffer.from(await blob.arrayBuffer());
}

function parseNdjson(ndjson) {
  return (ndjson || "")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function replaceMany(text, replacements) {
  let revised = text;
  for (const [before, after] of replacements) {
    revised = revised.replaceAll(before, after);
  }
  return revised;
}

function standardizeGeneSetTerms(text, slideNumber) {
  if ([6, 7].includes(slideNumber)) return text;
  let revised = replaceMany(text, [
    ["13 OXPHOS genes encoded by mitochondrial DNA", "13 core MT genes"],
    ["13 OXPHOS subunits encoded by mitochondrial DNA", "13 core MT genes"],
    ["86 structural OXPHOS genes encoded by nuclear DNA", "86 nuclear-encoded OXPHOS genes"],
    ["structural OXPHOS genes encoded by nuclear DNA", "nuclear-encoded OXPHOS genes"],
    ["Structural OXPHOS genes encoded by nuclear DNA", "Nuclear-encoded OXPHOS genes"],
    ["nuclear-encoded structural OXPHOS gene expression", "nuclear-encoded OXPHOS gene expression"],
    ["Nuclear-encoded structural OXPHOS gene expression", "Nuclear-encoded OXPHOS gene expression"],
    ["nuclear-encoded structural OXPHOS genes", "nuclear-encoded OXPHOS genes"],
    ["Nuclear-encoded structural OXPHOS genes", "Nuclear-encoded OXPHOS genes"],
    ["nuclear structural OXPHOS genes", "nuclear-encoded OXPHOS genes"],
    ["Nuclear structural OXPHOS genes", "Nuclear-encoded OXPHOS genes"],
    ["nuclear structural OXPHOS", "nuclear-encoded OXPHOS"],
    ["Nuclear structural OXPHOS", "Nuclear-encoded OXPHOS"],
    ["nuclear-OXPHOS-up", "nuclear-encoded OXPHOS upregulation"],
    ["nuclear-OXPHOS-down", "nuclear-encoded OXPHOS downregulation"],
    ["nuclear OXPHOS-up", "nuclear-encoded OXPHOS upregulation"],
    ["nuclear OXPHOS-down", "nuclear-encoded OXPHOS downregulation"],
    ["Nuclear-OXPHOS", "Nuclear-encoded OXPHOS"],
    ["nuclear-OXPHOS", "nuclear-encoded OXPHOS"],
    ["Nuclear OXPHOS", "Nuclear-encoded OXPHOS"],
    ["nuclear OXPHOS", "nuclear-encoded OXPHOS"],
    ["mtDNA-encoded OXPHOS gene expression", "core MT gene expression"],
    ["mtDNA-encoded OXPHOS genes", "core MT genes"],
    ["mtDNA-encoded OXPHOS", "core MT genes"],
    ["mitochondrial-DNA-encoded OXPHOS genes", "core MT genes"],
    ["Mitochondrial-DNA-encoded OXPHOS genes", "Core MT genes"],
    ["Mitochondrial-DNA OXPHOS", "Core MT genes"],
    ["mitochondrial-DNA OXPHOS", "core MT genes"],
    ["mitochondrial-genome OXPHOS occurrences", "core MT gene occurrences"],
    ["Mitochondrial-genome OXPHOS occurrences", "Core MT gene occurrences"],
    ["mtDNA-OXPHOS DEG occurrences", "core MT gene DEG occurrences"],
    ["mtDNA-OXPHOS occurrences", "core MT gene occurrences"],
    ["mtDNA-OXPHOS genes", "core MT genes"],
    ["mtDNA-OXPHOS enrichment", "core MT gene enrichment"],
    ["mtDNA-OXPHOS increase", "core MT gene increase"],
    ["mtDNA-OXPHOS pattern", "core MT gene pattern"],
    ["mtDNA OXPHOS genes", "core MT genes"],
    ["mtDNA OXPHOS pattern", "core MT gene pattern"],
    ["mtDNA OXPHOS", "core MT genes"],
    ["mtDNA-up", "core MT upregulation"],
    ["mtDNA-down", "core MT downregulation"],
    ["mtDNA program", "core MT gene pattern"],
    ["mtDNA pattern", "core MT gene pattern"],
    ["mtDNA result", "core MT gene result"],
    ["mtDNA component", "core MT component"],
    ["mtDNA query genes", "core MT genes in the query"],
    ["mtDNA proteins", "proteins encoded by core MT genes"],
    ["mtDNA NES", "core MT NES"],
    ["mtDNA genes", "core MT genes"],
    ["mtDNA parts", "core MT genes"],
    ["mitochondrial-encoded genes", "core MT genes"],
    ["Mitochondrial-encoded genes", "Core MT genes"],
    ["mitochondrial-encoded parts", "core MT subunits"],
    ["Mitochondrial-encoded parts", "Core MT subunits"],
    ["the mitochondrial-DNA-encoded genes", "the core MT genes"],
    ["the mitochondrial-DNA set", "the core MT gene set"],
    ["the nuclear-DNA set", "the nuclear-encoded OXPHOS gene set"],
    ["mitochondrial-DNA occurrences", "core MT gene occurrences"],
    ["nuclear-DNA occurrences", "nuclear-encoded OXPHOS gene occurrences"],
    ["Mitochondrial DEG-program finding.", "Mitochondrial pathway finding based on DEGs."],
    ["mitochondrial DEG-program finding", "mitochondrial pathway finding based on DEGs"],
    ["program-level agreement", "gene-set-level agreement"],
    ["Program-level agreement", "Gene-set-level agreement"],
    ["program-level support", "gene-set-level support"],
    ["Program-level support", "Gene-set-level support"],
    ["program-level results", "gene-set-level results"],
    ["Program-level results", "Gene-set-level results"],
    ["program evidence", "gene-set evidence"],
    ["Program evidence", "Gene-set evidence"],
    ["program support", "gene-set support"],
    ["Program support", "Gene-set support"],
    ["query program", "query gene set"],
    ["downward program", "downward OXPHOS pattern"],
    ["female ε2 program", "female ε2 OXPHOS pattern"],
    ["matched inhibitory-neuron program", "matched inhibitory-neuron gene-set pattern"],
    ["PROGRAM ENRICHMENT", "PATHWAY ENRICHMENT"],
    ["PROGRAM COMPARISON", "GENE-SET COMPARISON"],
    ["Two mitochondrial programs", "Two mitochondrial gene-set patterns"],
    ["similar mitochondrial programs", "similar mitochondrial gene-set patterns"],
    ["Female ε3/ε3 program", "Female ε3/ε3 pattern"],
    ["Male ε3/ε3 program", "Male ε3/ε3 pattern"],
  ]);
  revised = revised
    .replaceAll("core MT genes gene", "core MT gene")
    .replaceAll("core MT genes pattern", "core MT gene pattern")
    .replaceAll("core MT genes result", "core MT gene result")
    .replaceAll("core MT genes enrichment", "core MT gene enrichment")
    .replaceAll("core MT genes increase", "core MT gene increase")
    .replaceAll("core MT genes occurrences", "core MT gene occurrences")
    .replaceAll("core MT genes component", "core MT component")
    .replaceAll("core MT genes is", "core MT genes are")
    .replaceAll("nuclear-encoded OXPHOS genes genes", "nuclear-encoded OXPHOS genes");
  return revised;
}

const VISIBLE_OVERRIDES = new Map([
  [
    "8|mitocarta-hierarchy-subtitle",
    "MitoCarta organizes its 1,136 MT genes into nested pathways, from broad systems to detailed subpathways.",
  ],
  ["10|TextBox 4", "Core MT genes"],
  ["10|TextBox 8", "The 13 core MT genes encode structural OXPHOS subunits."],
  ["10|TextBox 10", "Nuclear-encoded OXPHOS genes"],
  ["10|TextBox 14", "The 86 genes encode structural respiratory-complex subunits."],
  ["13|direction-example-label", "Example: male ε3/ε3, core MT genes"],
  ["13|up-share-example-label", "Example: male ε3/ε3, core MT genes"],
  [
    "14|TextBox 6",
    "Female ε3/ε3: both OXPHOS sets mostly rise; male ε3/ε3: core MT genes rise while nuclear-encoded OXPHOS genes fall.",
  ],
  [
    "14|up-share-key-contrast-text",
    "Female ε3/ε3: both OXPHOS sets mostly rise. Male ε3/ε3: core MT genes rise while nuclear-encoded OXPHOS genes fall.",
  ],
  ["43|TextBox 3", "Female APOE ε3/ε3 cells show strong core MT gene upregulation"],
  [
    "43|TextBox 4",
    "A mitochondrial DEG finding with secondary nuclear-encoded OXPHOS support in ROSMAP.",
  ],
  [
    "43|TextBox 20",
    "SEA-AD supports the core MT gene pattern. Nuclear-encoded OXPHOS support is currently ROSMAP-only.",
  ],
  ["44|TextBox 1", "Female ε3/ε3 cells show higher core MT gene expression in AD"],
  [
    "44|TextBox 2",
    "The core MT gene result repeats across ROSMAP fine-cell comparisons and receives support from SEA-AD.",
  ],
  ["44|TextBox 12", "CORE MT GENES"],
  ["44|TextBox 13", "13 protein-coding genes\nencoded by mtDNA"],
  [
    "44|TextBox 17",
    "higher core MT gene expression\nin AD than in the comparison group",
  ],
  [
    "44|TextBox 19",
    "Nuclear-encoded OXPHOS gene expression also rises in ROSMAP, but cross-cohort support is strongest for core MT genes.",
  ],
  ["45|TextBox 5", "Core MT genes\n217/217 occurrences are AD-up"],
  ["45|TextBox 6", "Nuclear-encoded OXPHOS genes\n76/89 occurrences are AD-up (85%)"],
  ["45|TextBox 14", "core MT gene DEG occurrences"],
  [
    "45|TextBox 23",
    "Enriched = more core MT genes than expected by chance in the exact background (BH-adjusted P < 0.05). Tested genes are the MitoCarta MT genes in the KDA query.",
  ],
  [
    "46|TextBox 1",
    "SEA-AD adds strong support for the excitatory-neuron core MT gene pattern",
  ],
  ["46|TextBox 5", "SEA query genes include nine shared core MT genes"],
  ["47|TextBox 11", "Essential core MT genes"],
  [
    "47|TextBox 12",
    "The 13 core MT genes encode structural OXPHOS subunits needed for respiration.",
  ],
  [
    "47|TextBox 17",
    "Core MT genes are mostly upregulated in both cohorts. Nuclear-encoded OXPHOS genes are also mostly upregulated in ROSMAP.",
  ],
  ["48|TextBox 9", "Does not test this exact core MT gene pattern."],
  [
    "49|TextBox 3",
    "Male APOE ε3/ε3 cells show opposite core MT and nuclear-encoded OXPHOS directions",
  ],
  [
    "49|TextBox 4",
    "A mitochondrial pathway finding based on DEGs, not an identified upstream key driver.",
  ],
  [
    "50|TextBox 2",
    "The two OXPHOS gene sets often move in opposite directions. Matched inhibitory neurons show the pattern in SEA-AD.",
  ],
  ["50|TextBox 12", "CORE MT GENES"],
  ["50|TextBox 14", "core MT gene expression"],
  ["50|TextBox 16", "NUCLEAR-ENCODED OXPHOS GENES"],
  ["50|TextBox 18", "nuclear-encoded OXPHOS gene expression"],
  ["51|TextBox 5", "Core MT genes"],
  ["51|TextBox 17", "Nuclear-encoded OXPHOS genes"],
  [
    "52|TextBox 1",
    "SEA-AD supports the matched male ε3/ε3 inhibitory-neuron gene-set pattern",
  ],
  [
    "52|TextBox 2",
    "8 matched KDA calls were evaluable. Support is gene-set-level rather than replication of the same gene returned from KDA calls.",
  ],
  ["52|TextBox 5", "shared MitoCarta MT query genes"],
  ["52|TextBox 14", "CORE MT GENES"],
  ["52|TextBox 16", "9 core MT genes are AD-up in both cohorts"],
  ["53|TextBox 5", "9 core MT genes ↑ in both"],
  ["53|TextBox 26", "8 nuclear-encoded MitoCarta MT genes ↓ in both"],
  [
    "54|TextBox 7",
    "OXPHOS complexes combine proteins encoded by core MT genes and nuclear-encoded OXPHOS genes.",
  ],
  [
    "55|TextBox 7",
    "OXPHOS requires coordinated core MT and nuclear-encoded OXPHOS subunits.",
  ],
  ["56|TextBox 4", "Mitochondrial pathway finding based on DEGs."],
  [
    "56|TextBox 20",
    "Both core MT and nuclear-encoded OXPHOS genes were mostly upregulated in female ε2 cells.",
  ],
  ["57|TextBox 12", "CORE MT GENES"],
  ["57|TextBox 14", "The 13 core MT genes encode structural OXPHOS subunits."],
  ["57|TextBox 16", "NUCLEAR-ENCODED OXPHOS"],
  [
    "57|TextBox 18",
    "The 86 nuclear-encoded OXPHOS genes supply most structural subunits.",
  ],
  ["58|TextBox 5", "core MT gene occurrences"],
  ["58|TextBox 9", "nuclear-encoded OXPHOS gene occurrences"],
  ["58|TextBox 14", "20 core MT, 9 nuclear-encoded"],
  ["58|TextBox 16", "Core MT genes"],
  ["58|TextBox 20", "Nuclear-encoded OXPHOS genes"],
  [
    "58|TextBox 26",
    "core MT and nuclear-encoded OXPHOS upregulation, respectively",
  ],
  [
    "59|TextBox 6",
    "Nine of 12 fine types enriched core MT upregulation and eight of 12 enriched nuclear-encoded OXPHOS upregulation.",
  ],
  [
    "59|TextBox 10",
    "Excitatory nuclear-encoded OXPHOS remained strongly up, while the core MT component was not significant.",
  ],
  [
    "60|TextBox 1",
    "Why this matters: an ε2-associated response may coordinate both OXPHOS gene sets",
  ],
  [
    "63|TextBox 3",
    "Female APOE ε4 fine-cell results show a strong nuclear-encoded OXPHOS decrease",
  ],
  ["63|TextBox 4", "Mitochondrial pathway finding based on DEGs."],
  [
    "64|TextBox 2",
    "Nuclear-encoded OXPHOS genes are strongly downward, while core MT genes show mixed directions.",
  ],
  ["64|TextBox 12", "NUCLEAR-ENCODED OXPHOS"],
  [
    "64|TextBox 14",
    "Most structural respiratory-complex subunit genes are nuclear-encoded.",
  ],
  ["64|TextBox 16", "CORE MT GENES"],
  [
    "64|TextBox 18",
    "Core MT genes contribute 26 upregulated and 38 downregulated occurrences.",
  ],
  [
    "64|TextBox 22",
    "The result should not be described as a uniform decrease of all MitoCarta MT genes.",
  ],
  [
    "65|TextBox 1",
    "ROSMAP: 95% of female ε4 nuclear-encoded OXPHOS occurrences are AD-down",
  ],
  [
    "65|TextBox 2",
    "The core MT component is smaller and more mixed than the nuclear-encoded component.",
  ],
  ["65|TextBox 5", "nuclear-encoded OXPHOS gene occurrences"],
  ["65|TextBox 9", "core MT gene occurrences"],
  ["65|TextBox 16", "Nuclear-encoded OXPHOS genes"],
  [
    "65|TextBox 18",
    "Six eligible KDA calls showed significant nuclear-encoded OXPHOS enrichment",
  ],
  ["65|TextBox 20", "Core MT genes"],
  [
    "65|TextBox 26",
    "Four of 13 testable excitatory fine types enriched nuclear-encoded OXPHOS downregulation",
  ],
  [
    "66|TextBox 6",
    "Excitatory nuclear-encoded OXPHOS NES was +0.70 with local BH 0.991.",
  ],
  [
    "66|TextBox 10",
    "Excitatory nuclear-encoded OXPHOS NES was +2.01 with local BH 5.62 × 10⁻⁵.",
  ],
  [
    "67|TextBox 1",
    "Why this matters: most respiratory-complex genes are nuclear-encoded",
  ],
  ["68|TextBox 11", "A uniform decrease across all MitoCarta MT genes"],
  [
    "69|TextBox 9",
    "Does not reproduce the nuclear-encoded OXPHOS gene-expression pattern.",
  ],
  [
    "70|TextBox 3",
    "Male APOE ε2 cells show broad decreases across both OXPHOS gene sets",
  ],
  ["70|TextBox 4", "Mitochondrial pathway finding based on DEGs."],
  ["71|TextBox 12", "CORE MT GENES"],
  [
    "71|TextBox 14",
    "About 90% of core MT gene occurrences were lower in AD.",
  ],
  ["71|TextBox 16", "NUCLEAR-ENCODED OXPHOS"],
  [
    "71|TextBox 18",
    "About 87% of nuclear-encoded OXPHOS gene occurrences were lower in AD.",
  ],
  [
    "71|TextBox 22",
    "Both OXPHOS gene sets move downward, unlike the opposite-direction pattern in male ε3/ε3.",
  ],
  ["72|TextBox 5", "core MT gene occurrences"],
  ["72|TextBox 9", "nuclear-encoded OXPHOS gene occurrences"],
  ["72|TextBox 14", "12 core MT, 17 nuclear-encoded"],
  ["72|TextBox 16", "Core MT genes"],
  ["72|TextBox 20", "Nuclear-encoded OXPHOS genes"],
  [
    "72|TextBox 26",
    "core MT and nuclear-encoded OXPHOS downregulation, respectively",
  ],
  [
    "77|TextBox 3",
    "Male APOE ε4 cells may show opposite core MT and nuclear-encoded OXPHOS directions",
  ],
  ["77|TextBox 4", "Mitochondrial pathway finding based on DEGs."],
  [
    "77|TextBox 20",
    "Core MT genes are mostly upregulated and nuclear-encoded OXPHOS genes are modestly downregulated, with mixed cross-cohort sensitivity.",
  ],
  ["78|TextBox 12", "CORE MT GENES"],
  [
    "78|TextBox 14",
    "Core MT gene expression mostly increases in AD.",
  ],
  ["78|TextBox 16", "NUCLEAR-ENCODED OXPHOS"],
  [
    "78|TextBox 18",
    "Nuclear-encoded OXPHOS gene expression tends to decrease, but less consistently.",
  ],
  [
    "79|TextBox 1",
    "ROSMAP: male ε4 shows clear core MT upregulation and modest nuclear-encoded OXPHOS downregulation",
  ],
  ["79|TextBox 5", "core MT gene occurrences"],
  ["79|TextBox 9", "nuclear-encoded OXPHOS gene occurrences"],
  ["79|TextBox 14", "core MT gene enrichment"],
  ["79|TextBox 16", "Core MT genes"],
  ["79|TextBox 20", "Nuclear-encoded OXPHOS genes"],
  ["80|TextBox 5", "+2.03 core MT NES"],
  [
    "80|TextBox 6",
    "The core MT upregulation component survived composition adjustment.",
  ],
  [
    "81|TextBox 6",
    "Both findings place core MT genes upward and nuclear-encoded OXPHOS genes downward.",
  ],
  [
    "84|TextBox 3",
    "A cytosolic-ribosome module repeatedly connects to nuclear-encoded OXPHOS genes",
  ],
  [
    "84|TextBox 20",
    "RPL11, RPS15, and related cytosolic ribosome genes recur near nuclear-encoded OXPHOS query genes.",
  ],
  [
    "85|TextBox 1",
    "Cytosolic ribosome genes repeatedly connect to nuclear-encoded OXPHOS query genes",
  ],
  ["85|TextBox 17", "Nuclear-encoded OXPHOS genes"],
  [
    "87|TextBox 2",
    "RPL11 has a broad nuclear-encoded OXPHOS neighborhood, while RPS15 recurs across the most categories.",
  ],
  [
    "87|TextBox 10",
    "Nuclear-encoded OXPHOS contributes 151 overlaps, including 100 AD-down occurrences.",
  ],
  [
    "91|TextBox 20",
    "LAMTOR5 repeatedly links lysosomal nutrient sensing with mostly decreased nuclear-encoded OXPHOS genes.",
  ],
  ["92|TextBox 10", "Nuclear-encoded OXPHOS genes"],
  ["92|TextBox 21", "Mostly decreased nuclear-encoded OXPHOS genes"],
  [
    "92|TextBox 1",
    "LAMTOR5 connects lysosomal nutrient sensing with nuclear-encoded OXPHOS genes",
  ],
  ["93|TextBox 10", "39 nuclear-encoded OXPHOS"],
  ["93|TextBox 14", "nuclear-encoded OXPHOS"],
  ["93|TextBox 16", "Nuclear-encoded OXPHOS genes"],
  [
    "98|TextBox 3",
    "WDR82 is linked to a narrow excitatory-neuron core MT upregulation module",
  ],
  [
    "98|TextBox 20",
    "WDR82 appears only in excitatory neurons and sits near a four-gene core MT upregulation neighborhood.",
  ],
  [
    "99|TextBox 1",
    "WDR82 sits near a focused core MT upregulation signal in excitatory neurons",
  ],
  [
    "99|TextBox 2",
    "The exact neighborhood is narrow, and four recurring core MT genes originate within one long mitochondrial RNA.",
  ],
  ["99|TextBox 8", "Four core MT genes"],
  [
    "99|TextBox 18",
    "These four core MT genes account for nearly every exact KDA overlap.",
  ],
  [
    "100|TextBox 1",
    "ROSMAP: every WDR82-supporting query shows enriched core MT upregulation",
  ],
  ["100|TextBox 9", "core MT gene occurrences"],
  ["100|TextBox 14", "Core MT genes"],
  [
    "101|TextBox 16",
    "WDR82 could have been returned from a KDA call in 11 matching SEA-AD excitatory backgrounds but was not, although SEA-AD supports the female ε3/ε3 core MT gene pattern.",
  ],
  [
    "102|TextBox 6",
    "WDR82 could indirectly affect mitochondrial pathways through nuclear regulation.",
  ],
  [
    "102|TextBox 10",
    "A repeated core MT gene cluster may track overall mitochondrial RNA abundance or sample quality.",
  ],
  [
    "102|TextBox 17",
    "Removing core MT genes from the queries is an important sensitivity test before mechanistic interpretation.",
  ],
  ["103|TextBox 16", "Make KDA calls without core MT genes in the queries"],
  [
    "104|TextBox 14",
    "Shows that core MT genes are transcribed within long polycistronic RNAs.",
  ],
  [
    "106|TextBox 18",
    "Mitochondrial ribosomes and factors build proteins encoded by core MT genes.",
  ],
  ["107|TextBox 14", "nuclear-encoded OXPHOS"],
  ["109|TextBox 9", "Translation supplies proteins encoded by core MT genes"],
  ["114|TextBox 14", "nuclear-encoded OXPHOS"],
  ["117|TextBox 7", "Control of the listed MitoCarta MT genes in human neurons"],
  ["128|TextBox 14", "core MT and nuclear-encoded OXPHOS genes"],
  [
    "136|TextBox 1",
    "The broader queries support core MT gene enrichment, but not a PLCG2 mechanism",
  ],
  ["136|TextBox 5", "41 core MT gene occurrences"],
  [
    "136|TextBox 6",
    "The six full queries contain 36 AD-up and five AD-down core MT gene occurrences.",
  ],
  ["136|TextBox 8", "PATHWAY ENRICHMENT"],
  [
    "136|TextBox 10",
    "All six input queries show significant core MT gene enrichment.",
  ],
  ["142|TextBox 26", "Nuclear-encoded OXPHOS genes also appear"],
  ["145|TextBox 7", "That APOE regulates neighboring MitoCarta MT genes"],
  [
    "154|TextBox 3",
    "SEA-AD provides gene-set and cross-context support despite no exact driver matches",
  ],
  [
    "154|TextBox 20",
    "Mitochondrial gene-set patterns agree more strongly than exact driver identities across the two cohort-specific network analyses.",
  ],
  [
    "155|TextBox 1",
    "ROSMAP and SEA-AD agree more on mitochondrial gene-set patterns than on exact drivers",
  ],
  ["155|TextBox 20", "GENE-SET COMPARISON"],
  [
    "155|TextBox 22",
    "Female ε3/ε3 and male ε3/ε3 gene-set evidence remains the strongest cross-cohort result.",
  ],
  [
    "158|TextBox 6",
    "Cohort-specific networks can place different genes near the same query gene set.",
  ],
  ["158|TextBox 13", "Two mitochondrial gene-set patterns"],
  [
    "158|TextBox 17",
    "Gene-set support can strengthen a ROSMAP finding without confirming its exact upstream candidate.",
  ],
  [
    "159|TextBox 11",
    "A shared upstream cause for similar mitochondrial gene-set patterns",
  ],
  ["160|TextBox 4", "Female ε3/ε3 pattern"],
  [
    "160|TextBox 7",
    "Nine shared core MT genes are AD-up in both cohorts and overlap BH is 0.00505.",
  ],
  ["160|TextBox 11", "Male ε3/ε3 pattern"],
]);

function refineVisibleText(record) {
  const override = VISIBLE_OVERRIDES.get(`${record.slide}|${record.name}`);
  if (override !== undefined) return override;
  let revised = standardizeGeneSetTerms(record.text, record.slide);
  if (record.slide === 62) {
    revised = revised.replaceAll("this exact female ε2 program", "this exact female ε2 OXPHOS pattern");
  }
  if (record.slide === 74) {
    revised = revised.replaceAll("The downward program", "The downward OXPHOS pattern");
  }
  if (record.slide === 75) {
    revised = revised.replaceAll("the downward program", "the downward OXPHOS pattern");
  }
  if (record.slide === 101) {
    revised = revised.replaceAll("the strongest program support", "the strongest gene-set support");
  }
  return revised;
}

function refineNotes(slideNumber, text) {
  let revised = standardizeGeneSetTerms(text, slideNumber);
  if ([6, 7].includes(slideNumber)) return revised;
  revised = replaceMany(revised, [
    [
      "Mitochondrial DNA encodes 13 protein subunits of oxidative phosphorylation, or OXPHOS.",
      "The 13 core MT genes encode structural subunits of oxidative phosphorylation, or OXPHOS.",
    ],
    [
      "Mitochondrial DNA encodes 13 core OXPHOS subunits needed by the respiratory system.",
      "The 13 core MT genes encode structural OXPHOS subunits needed by the respiratory system.",
    ],
    [
      "The mitochondrial genome encodes 13 core OXPHOS subunits needed by the respiratory system.",
      "The 13 core MT genes encode structural OXPHOS subunits needed by the respiratory system.",
    ],
    [
      "The matched inhibitory-neuron gene-set pattern also appears in SEA-AD.",
      "The matched inhibitory-neuron gene-set pattern also appears in SEA-AD.",
    ],
    [
      "This is a transcript-level mitochondrial program.",
      "This is a transcript-level pattern across mitochondrial gene sets.",
    ],
    [
      "mitochondrial gene programs",
      "mitochondrial gene-set patterns",
    ],
    [
      "mitochondrial programs",
      "mitochondrial gene-set patterns",
    ],
  ]);
  if (slideNumber === 5) {
    revised = revised.replaceAll(
      "including core MT genes, nuclear-encoded OXPHOS, mitochondrial translation, and MICOS or inner-membrane organization",
      "including the core MT gene set, nuclear-encoded OXPHOS genes, mitochondrial translation, and MICOS or inner-membrane organization",
    );
  }
  if (slideNumber === 8) {
    revised = revised.replaceAll(
      "MitoCarta organizes mitochondrial genes into a nested hierarchy.",
      "MitoCarta organizes its 1,136 MT genes into a nested hierarchy.",
    );
  }
  if (slideNumber === 10) {
    revised = revised.replaceAll(
      "The first contains the 13 core MT genes. The second contains 86 nuclear-encoded OXPHOS subunits encoded by nuclear DNA.",
      "The first is the 13-gene core MT set. The second contains the 86 nuclear-encoded OXPHOS genes.",
    );
    revised = revised.replaceAll(
      "The first contains the 13 core MT genes. The second contains 86 structural OXPHOS subunits encoded by nuclear DNA.",
      "The first is the 13-gene core MT set. The second contains the 86 nuclear-encoded OXPHOS genes.",
    );
  }
  if (slideNumber === 14) {
    revised = revised.replaceAll(
      "the mitochondrial-DNA set",
      "the core MT gene set",
    );
    revised = revised.replaceAll(
      "the nuclear-DNA set",
      "the nuclear-encoded OXPHOS gene set",
    );
  }
  if (slideNumber === 42) {
    revised = revised.replaceAll(
      "the female epsilon-3 homozygous core MT genes increase",
      "the female epsilon-3 homozygous core MT gene increase",
    );
  }
  if (slideNumber === 43) {
    revised = revised.replaceAll(
      "a strong core MT genes increase",
      "strong core MT gene upregulation",
    );
  }
  if (slideNumber === 44) {
    revised = revised.replaceAll(
      "the mitochondrial-DNA-encoded genes",
      "the core MT genes",
    );
  }
  if (slideNumber === 45) {
    revised = revised.replaceAll(
      "core MT genes appear 217 times",
      "core MT genes contribute 217 occurrences",
    );
    revised = revised.replaceAll(
      "nuclear-encoded OXPHOS genes appear 89 times",
      "nuclear-encoded OXPHOS genes contribute 89 occurrences",
    );
  }
  if (slideNumber === 49) {
    revised = revised.replaceAll(
      "opposite directions in gene expression across the two genomes that encode oxidative-phosphorylation machinery",
      "opposite gene-expression directions across the core MT and nuclear-encoded OXPHOS gene sets",
    );
  }
  if (slideNumber === 52) {
    revised = revised.replaceAll(
      "what gene-set-level agreement means here",
      "what gene-set-level agreement means here",
    );
  }
  if (slideNumber === 53) {
    revised = revised.replaceAll(
      "Eight nuclear or mitochondrial-maintenance genes were downregulated in both",
      "Eight nuclear-encoded MitoCarta MT genes were downregulated in both",
    );
  }
  if (slideNumber === 54) {
    revised = revised.replaceAll(
      "OXPHOS complexes combine proteins encoded by mitochondrial DNA with proteins encoded by nuclear DNA",
      "OXPHOS complexes combine proteins encoded by core MT genes with proteins encoded by nuclear-encoded OXPHOS genes",
    );
  }
  if (slideNumber === 55) {
    revised = revised.replaceAll(
      "coordinated core MT subunits and nuclear-encoded parts",
      "coordinated core MT and nuclear-encoded OXPHOS subunits",
    );
  }
  if (slideNumber === 56) {
    revised = revised.replaceAll(
      "both core MT genes and nuclear-encoded OXPHOS genes",
      "both core MT and nuclear-encoded OXPHOS genes",
    );
  }
  if (slideNumber === 64) {
    revised = revised.replaceAll(
      "The nuclear side is strongly downward",
      "Nuclear-encoded OXPHOS gene expression is strongly downward",
    );
  }
  if (slideNumber === 67) {
    revised = revised.replaceAll(
      "A nuclear-sided reduction could reflect",
      "Lower nuclear-encoded OXPHOS gene expression could reflect",
    );
  }
  if (slideNumber === 70) {
    revised = revised.replaceAll(
      "both core MT genes and nuclear-encoded OXPHOS genes",
      "both core MT and nuclear-encoded OXPHOS genes",
    );
  }
  if (slideNumber === 77) {
    revised = revised.replaceAll(
      "core MT genes are mostly up and nuclear-encoded OXPHOS is modestly down",
      "core MT genes are mostly upregulated and nuclear-encoded OXPHOS genes are modestly downregulated",
    );
  }
  if (slideNumber === 99) {
    revised = revised.replaceAll(
      "four recurring mitochondrial genes begin within one long mitochondrial RNA",
      "four recurring core MT genes originate within one long mitochondrial RNA",
    );
  }
  if (slideNumber === 101) {
    revised = revised.replaceAll(
      "although it supports the female ε3/ε3 core MT gene pattern",
      "although SEA-AD supports the female ε3/ε3 core MT gene pattern",
    );
  }
  if (slideNumber === 102) {
    revised = revised.replaceAll(
      "mitochondrial gene-set patterns through nuclear regulation",
      "mitochondrial pathways through nuclear regulation",
    );
  }
  if (slideNumber === 154) {
    revised = revised.replaceAll(
      "Programs agree more strongly",
      "Mitochondrial gene-set patterns agree more strongly",
    );
  }
  if (slideNumber === 158) {
    revised = revised.replaceAll(
      "Gene-set support can strengthen",
      "Gene-set support can strengthen",
    );
  }
  if (slideNumber === 160) {
    revised = revised.replaceAll(
      "the strongest gene-set-level results",
      "the strongest gene-set-level results",
    );
  }
  return revised;
}

function relationshipAttributes(tag) {
  return Object.fromEntries(
    [...tag.matchAll(/([A-Za-z:]+)="([^"]*)"/g)].map((match) => [match[1], match[2]]),
  );
}

function relationshipPartPath(ownerPartPath) {
  return path.posix.join(
    path.posix.dirname(ownerPartPath),
    "_rels",
    `${path.posix.basename(ownerPartPath)}.rels`,
  );
}

function targetPartPath(ownerPartPath, target) {
  if (target.startsWith("/")) return target.slice(1);
  return path.posix.normalize(path.posix.join(path.posix.dirname(ownerPartPath), target));
}

async function orderedSlidePartPaths(zip) {
  const presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  const presentationRels = await zip.file("ppt/_rels/presentation.xml.rels")?.async("string");
  if (!presentationXml || !presentationRels) {
    throw new Error("Presentation ordering metadata is missing");
  }
  const slideIds = [
    ...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g),
  ].map((match) => match[1]);
  const relationships = [
    ...presentationRels.matchAll(/<Relationship\b[^>]*\/?\s*>/g),
  ].map((match) => relationshipAttributes(match[0]));
  return slideIds.map((relationshipId) => {
    const relation = relationships.find(
      (item) => item.Id === relationshipId && item.Type?.endsWith("/slide"),
    );
    if (!relation?.Target) throw new Error(`Slide relationship ${relationshipId} was not found`);
    return relation.Target.startsWith("/")
      ? relation.Target.slice(1)
      : path.posix.normalize(path.posix.join("ppt", relation.Target));
  });
}

async function relationshipsForPart(zip, ownerPartPath) {
  const relsXml = await zip.file(relationshipPartPath(ownerPartPath))?.async("string");
  if (!relsXml) throw new Error(`Missing relationships for ${ownerPartPath}`);
  return [...relsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map((match) =>
    relationshipAttributes(match[0]),
  );
}

async function relatedPartForSlide(zip, slidePart, typeSuffix) {
  const relationships = await relationshipsForPart(zip, slidePart);
  const relation = relationships.find((item) => item.Type?.endsWith(typeSuffix));
  if (!relation?.Target) throw new Error(`No ${typeSuffix} relationship for ${slidePart}`);
  return targetPartPath(slidePart, relation.Target);
}

async function notesPartForSlide(zip, slidePart) {
  return relatedPartForSlide(zip, slidePart, "/notesSlide");
}

async function remapSlideRelationshipIds({
  sourceZip,
  artifactZip,
  sourceSlidePart,
  artifactSlidePart,
  artifactSlideXml,
}) {
  const sourceRelationships = await relationshipsForPart(sourceZip, sourceSlidePart);
  const artifactRelationships = await relationshipsForPart(artifactZip, artifactSlidePart);
  let remapped = artifactSlideXml;
  for (const artifactRelation of artifactRelationships) {
    if (!artifactRelation.Id || !artifactRelation.Type || !artifactRelation.Target) continue;
    const artifactTarget = targetPartPath(artifactSlidePart, artifactRelation.Target);
    let sourceRelation = sourceRelationships.find(
      (item) =>
        item.Type === artifactRelation.Type &&
        item.Target &&
        targetPartPath(sourceSlidePart, item.Target) === artifactTarget,
    );
    if (!sourceRelation && artifactRelation.Type.endsWith("/chart")) {
      const chartRelations = sourceRelationships.filter((item) =>
        item.Type?.endsWith("/chart"),
      );
      if (chartRelations.length === 1) sourceRelation = chartRelations[0];
    }
    if (!sourceRelation?.Id) {
      throw new Error(
        `Could not map ${artifactRelation.Id} (${artifactRelation.Type}, ${artifactTarget}) on ${sourceSlidePart}`,
      );
    }
    remapped = remapped.replaceAll(artifactRelation.Id, sourceRelation.Id);
  }
  return remapped;
}

async function updateEmbeddedChartWorkbook(sourceZip, JSZip) {
  const workbookPath = "ppt/embeddings/Microsoft_Excel_Worksheet.xlsx";
  const workbookPart = sourceZip.file(workbookPath);
  if (!workbookPart) throw new Error(`Missing embedded workbook: ${workbookPath}`);
  const workbookZip = await JSZip.loadAsync(await workbookPart.async("nodebuffer"));
  const sheetPath = "xl/worksheets/sheet1.xml";
  let sheetXml = await workbookZip.file(sheetPath)?.async("string");
  if (!sheetXml) throw new Error(`Missing embedded workbook sheet: ${sheetPath}`);
  for (let index = 0; index < OLD_CHART_SERIES_NAMES.length; index += 1) {
    if (!sheetXml.includes(OLD_CHART_SERIES_NAMES[index])) {
      throw new Error(`Workbook is missing chart series name: ${OLD_CHART_SERIES_NAMES[index]}`);
    }
    sheetXml = sheetXml.replaceAll(
      OLD_CHART_SERIES_NAMES[index],
      CHART_SERIES_NAMES[index],
    );
  }
  workbookZip.file(sheetPath, sheetXml);
  sourceZip.file(
    workbookPath,
    await workbookZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );
  return workbookPath;
}

async function main() {
  const sourceStat = await fs.stat(SOURCE).catch(() => undefined);
  if (!sourceStat?.isFile()) throw new Error(`Missing source deck: ${SOURCE}`);
  if (await fs.stat(FINAL_PPTX).catch(() => undefined)) {
    throw new Error(`Output already exists: ${FINAL_PPTX}`);
  }
  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });

  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceHash = sha256(sourceBuffer);
  const { importRuntimeModule } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href
  );
  const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");
  const JSZipModule = await importRuntimeModule("jszip");
  const JSZip = JSZipModule.default ?? JSZipModule;
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const slides = slidesFromPresentation(presentation);
  if (slides.length !== EXPECTED_SLIDES) {
    throw new Error(`Expected ${EXPECTED_SLIDES} slides, found ${slides.length}`);
  }

  const textSnapshot = await presentation.inspect({
    kind: "textbox",
    include: "id,slide,name,text,textPreview,bbox",
    maxChars: 5000000,
  });
  const textChanges = [];
  for (const record of parseNdjson(textSnapshot.ndjson).filter(
    (item) => item.kind === "textbox" && typeof item.text === "string",
  )) {
    const revised = refineVisibleText(record);
    if (revised !== record.text) {
      textChanges.push({ ...record, revised });
    }
  }

  const notesSnapshot = await presentation.inspect({ kind: "notes", maxChars: 5000000 });
  const noteChanges = [];
  for (const record of parseNdjson(notesSnapshot.ndjson).filter(
    (item) => item.kind === "notes" && typeof item.text === "string",
  )) {
    const revised = refineNotes(record.slide, record.text);
    if (revised !== record.text) noteChanges.push({ ...record, revised });
  }

  if (!textChanges.length || !noteChanges.length) {
    throw new Error("Terminology audit did not identify both visible-text and speaker-note changes");
  }

  const changedVisibleSlides = new Set(textChanges.map((item) => item.slide));
  changedVisibleSlides.add(CHART_SLIDE);
  const changedNotesSlides = new Set(noteChanges.map((item) => item.slide));
  const beforePngs = new Map();
  for (const slideNumber of changedVisibleSlides) {
    const png = await blobBuffer(
      await presentation.export({ slide: slides[slideNumber - 1], format: "png", scale: 1.5 }),
    );
    beforePngs.set(slideNumber, png);
    await fs.writeFile(
      path.join(BUILD_DIR, `slide-${String(slideNumber).padStart(3, "0")}-before.png`),
      png,
    );
  }

  for (const change of textChanges) {
    const target = presentation.resolve(change.id);
    target.text.replace(change.text, change.revised);
    // These two labels contain hard line-break run boundaries, so a whole-text
    // assignment is needed to update both runs reliably.
    if (
      change.slide === 45 &&
      ["TextBox 5", "TextBox 6"].includes(change.name)
    ) {
      target.text = change.revised;
    }
  }
  for (const change of noteChanges) {
    slides[change.slide - 1].speakerNotes.textFrame.setText(change.revised);
    slides[change.slide - 1].speakerNotes.setVisible(true);
  }

  const chartSnapshot = await presentation.inspect({ kind: "chart", maxChars: 100000 });
  const chartRecord = parseNdjson(chartSnapshot.ndjson).find(
    (item) => item.kind === "chart" && item.slide === CHART_SLIDE,
  );
  if (!chartRecord?.id) throw new Error(`Could not find native chart on slide ${CHART_SLIDE}`);
  const chart = presentation.resolve(chartRecord.id);
  if (!Array.isArray(chart.series?.items) || chart.series.items.length !== 2) {
    throw new Error("Expected two native chart series on slide 14");
  }
  for (let index = 0; index < CHART_SERIES_NAMES.length; index += 1) {
    if (chart.series.items[index].name !== OLD_CHART_SERIES_NAMES[index]) {
      throw new Error(`Unexpected chart series ${index + 1}: ${chart.series.items[index].name}`);
    }
    chart.series.items[index].name = CHART_SERIES_NAMES[index];
  }

  await fs.writeFile(
    path.join(BUILD_DIR, "terminology-changes.json"),
    JSON.stringify(
      {
        sourceSha256: sourceHash,
        textChanges: textChanges.map(({ slide, name, text, revised }) => ({
          slide,
          name,
          before: text,
          after: revised,
        })),
        noteChanges: noteChanges.map(({ slide, text, revised }) => ({
          slide,
          before: text,
          after: revised,
        })),
        chartSeries: OLD_CHART_SERIES_NAMES.map((before, index) => ({
          before,
          after: CHART_SERIES_NAMES[index],
        })),
      },
      null,
      2,
    ) + "\n",
    "utf8",
  );

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source presentation changed during the terminology edit");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const sourceSlideParts = await orderedSlidePartPaths(sourceZip);
  const artifactSlideParts = await orderedSlidePartPaths(artifactZip);
  if (
    sourceSlideParts.length !== EXPECTED_SLIDES ||
    artifactSlideParts.length !== EXPECTED_SLIDES
  ) {
    throw new Error("Slide-order metadata changed unexpectedly");
  }

  const expectedChangedParts = new Set();
  for (const slideNumber of changedVisibleSlides) {
    const sourceSlidePart = sourceSlideParts[slideNumber - 1];
    const artifactSlidePart = artifactSlideParts[slideNumber - 1];
    const revisedXml = await artifactZip.file(artifactSlidePart)?.async("string");
    if (!revisedXml) throw new Error(`Missing revised slide XML for slide ${slideNumber}`);
    let remappedXml = await remapSlideRelationshipIds({
      sourceZip,
      artifactZip,
      sourceSlidePart,
      artifactSlidePart,
      artifactSlideXml: revisedXml,
    });
    if (slideNumber === CHART_SLIDE) {
      remappedXml = remappedXml
        .replaceAll("13 mitochondrial-DNA-encoded OXPHOS genes", "13 core MT genes")
        .replaceAll(
          "86 nuclear-DNA-encoded structural OXPHOS genes",
          "86 nuclear-encoded OXPHOS genes",
        );
    }
    sourceZip.file(sourceSlidePart, remappedXml);
    expectedChangedParts.add(sourceSlidePart);
  }
  for (const slideNumber of changedNotesSlides) {
    const sourceSlidePart = sourceSlideParts[slideNumber - 1];
    const artifactSlidePart = artifactSlideParts[slideNumber - 1];
    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const revisedXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!revisedXml) throw new Error(`Missing revised notes XML for slide ${slideNumber}`);
    sourceZip.file(sourceNotesPart, revisedXml);
    expectedChangedParts.add(sourceNotesPart);
  }

  const sourceChartPart = await relatedPartForSlide(
    sourceZip,
    sourceSlideParts[CHART_SLIDE - 1],
    "/chart",
  );
  const artifactChartPart = await relatedPartForSlide(
    artifactZip,
    artifactSlideParts[CHART_SLIDE - 1],
    "/chart",
  );
  const revisedChartXml = await artifactZip.file(artifactChartPart)?.async("string");
  if (!revisedChartXml) throw new Error(`Missing revised chart XML: ${artifactChartPart}`);
  for (const seriesName of CHART_SERIES_NAMES) {
    if (!revisedChartXml.includes(seriesName)) {
      throw new Error(`Artifact chart XML is missing revised series name: ${seriesName}`);
    }
  }
  // Keep the source chart package intact (especially its externalData workbook
  // relationship) and transplant only the two revised series labels. Artifact
  // Tool intentionally normalizes chart XML on export, which can otherwise
  // remove the embedded-workbook contract from an imported chart.
  let mergedChartXml = await sourceZip.file(sourceChartPart)?.async("string");
  if (!mergedChartXml) throw new Error(`Missing source chart XML: ${sourceChartPart}`);
  for (let index = 0; index < OLD_CHART_SERIES_NAMES.length; index += 1) {
    const before = OLD_CHART_SERIES_NAMES[index];
    const after = CHART_SERIES_NAMES[index];
    if (!mergedChartXml.includes(before)) {
      throw new Error(`Source chart XML is missing original series name: ${before}`);
    }
    mergedChartXml = mergedChartXml.replaceAll(before, after);
  }
  sourceZip.file(sourceChartPart, mergedChartXml);
  expectedChangedParts.add(sourceChartPart);
  expectedChangedParts.add(await updateEmbeddedChartWorkbook(sourceZip, JSZip));

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
    await sourceZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const validation = await finalizePresentation({
    explicitTotalSlideCount: EXPECTED_SLIDES,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [CHART_SLIDE],
    requiredEmbeddedWorkbookChartOwnerSlides: [CHART_SLIDE],
    nativeChartTargetApplication: "powerpoint",
    workspaceDir: WORKSPACE_DIR,
    candidatePath,
    finalPath: FINAL_PPTX,
    pythonExecutable:
      "/Users/rzhuang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12",
    integrityValidatorPath: path.join(
      SKILL_DIR,
      "container_tools/inspect_presentation_package_integrity.py",
    ),
    layoutValidatorPath: path.join(
      SKILL_DIR,
      "container_tools/inspect_presentation_layout_geometry.py",
    ),
    layoutArgs: [
      "--expected-slide-size-emu",
      "12192000,6858000",
      "--validate-bullet-geometry",
      "--validate-heading-fit",
    ],
    fontPolicy: {
      basis: "reference",
      families: ["Arial"],
      referencePath: SOURCE,
      referenceSha256: sourceHash,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD_DIR, "mito_gene_set_terms.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalTextSnapshot = await reopened.inspect({
    kind: "textbox,notes,chart,image",
    maxChars: 6000000,
  });
  const finalRecords = parseNdjson(finalTextSnapshot.ndjson);
  const residualPatterns = [
    /mtDNA-encoded OXPHOS/i,
    /mtDNA[- ]OXPHOS/i,
    /mitochondrial-DNA OXPHOS/i,
    /mitochondrial-DNA-encoded OXPHOS/i,
    /nuclear-DNA-encoded structural OXPHOS/i,
    /nuclear[- ]OXPHOS/i,
    /nuclear structural OXPHOS/i,
    /mitochondrial-encoded genes/i,
    /mitochondrial DEG-program/i,
    /mtDNA program/i,
    /program-level/i,
    /query program/i,
    /PROGRAM ENRICHMENT/,
    /PROGRAM COMPARISON/,
    /Two mitochondrial programs/,
    /mitochondrial energy genes/i,
    /nuclear or maintenance genes/i,
    /uniform decrease (?:of|across) all mitochondrial genes/i,
    /listed mitochondrial genes/i,
    /neighboring mitochondrial genes/i,
  ];
  const residuals = [];
  for (const record of finalRecords) {
    if ([6, 7].includes(record.slide)) continue;
    const text = [record.title, record.text, record.textPreview].filter(Boolean).join("\n");
    const matched = residualPatterns.filter((pattern) => pattern.test(text));
    if (matched.length) {
      residuals.push({
        slide: record.slide,
        kind: record.kind,
        name: record.name,
        text: record.text ?? record.title,
        patterns: matched.map(String),
      });
    }
  }
  if (residuals.length) {
    await fs.writeFile(
      path.join(BUILD_DIR, "terminology-residuals.json"),
      JSON.stringify(residuals, null, 2) + "\n",
      "utf8",
    );
    throw new Error(`Terminology audit found ${residuals.length} residual records`);
  }

  const finalChartSnapshot = await reopened.inspect({ kind: "chart", maxChars: 100000 });
  const finalChartRecord = parseNdjson(finalChartSnapshot.ndjson).find(
    (item) => item.kind === "chart" && item.slide === CHART_SLIDE,
  );
  const finalChart = reopened.resolve(finalChartRecord.id);
  const finalSeriesNames = finalChart.series.items.map((series) => series.name);
  if (JSON.stringify(finalSeriesNames) !== JSON.stringify(CHART_SERIES_NAMES)) {
    throw new Error(`Final chart series names are incorrect: ${JSON.stringify(finalSeriesNames)}`);
  }

  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const sourceFiles = Object.keys(originalZip.files)
    .filter((name) => !originalZip.files[name].dir)
    .sort();
  const actualChangedParts = [];
  for (const name of sourceFiles) {
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [before, after] = await Promise.all([
      originalZip.file(name).async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) actualChangedParts.push(name);
  }
  const expectedParts = [...expectedChangedParts].sort();
  if (
    actualChangedParts.length !== expectedParts.length ||
    actualChangedParts.some((part, index) => part !== expectedParts[index])
  ) {
    throw new Error(`Unexpected package changes: ${actualChangedParts.join(", ")}`);
  }

  for (const slideNumber of changedVisibleSlides) {
    const afterPng = await blobBuffer(
      await reopened.export({
        slide: reopened.slides.getItem(slideNumber - 1),
        format: "png",
        scale: 1.5,
      }),
    );
    await fs.writeFile(
      path.join(BUILD_DIR, `slide-${String(slideNumber).padStart(3, "0")}-after.png`),
      afterPng,
    );
    if (sha256(afterPng) === sha256(beforePngs.get(slideNumber))) {
      throw new Error(`Changed slide ${slideNumber} did not change visually`);
    }
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
        slideCount: EXPECTED_SLIDES,
        changedVisibleSlides: [...changedVisibleSlides].sort((a, b) => a - b),
        changedNotesSlides: [...changedNotesSlides].sort((a, b) => a - b),
        visibleTextChangeCount: textChanges.length,
        speakerNoteChangeCount: noteChanges.length,
        chartSeriesNames: finalSeriesNames,
        changedPackageParts: actualChangedParts,
        warnings: validation.warnings ?? [],
      },
      null,
      2,
    ),
  );
}

await main();
