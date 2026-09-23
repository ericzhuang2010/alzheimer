#!/usr/bin/env node

/** Apply the agreed "KDA calls" terminology to the five inserted summary slides. */

import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const WORKSPACE = "/Users/rzhuang/Documents/VscodeProjects/alzheimer";
const SKILL_DIR =
  "/Users/rzhuang/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations";
const SOURCE = path.join(
  WORKSPACE,
  "results/presentations/09162026_findings_summary_20260922_v3/output/09162026_sex_apoe_kda_fine_broad_findings_summary_20260922_v3.pptx",
);
const OUTPUT = path.join(
  WORKSPACE,
  "results/presentations/09162026_findings_summary_20260922_v5/output/09162026_sex_apoe_kda_fine_broad_findings_summary_20260922_v5.pptx",
);

const replacements = new Map([
  [
    "The findings separate into pre-network expression and pathway results, KDA network hypotheses, and cross-cohort validation.",
    "The findings separate into pre-network expression and pathway results, results from KDA calls, and cross-cohort validation.",
  ],
  ["KDA candidates", "Results from KDA calls"],
  [
    "Which network genes sit near MitoCarta MT DEGs?",
    "Which network genes are returned from KDA calls made with MitoCarta MT DEGs?",
  ],
  [
    "Walk through: Findings 1–6 come from differential-expression and pathway analyses before KDA. Findings 7–16 and 18 are KDA-based network hypotheses. Finding 17 evaluates cross-cohort support using SEA-AD.",
    "Walk through: Findings 1–6 come from differential-expression and pathway analyses before making KDA calls. Findings 7–16 and 18 summarize genes returned from KDA calls. Finding 17 evaluates cross-cohort support using SEA-AD.",
  ],
  [
    "These findings describe mitochondrial gene-expression and pathway patterns before KDA.",
    "These findings describe mitochondrial gene-expression and pathway patterns before making KDA calls.",
  ],
  ["KDA is not involved in Findings 1–6.", "KDA calls are not involved in Findings 1–6."],
  [
    "Teaching goal: Separate the direct DEG and pathway results from the later KDA findings.",
    "Teaching goal: Separate the direct DEG and pathway results from the later results of KDA calls.",
  ],
  [
    "Transition: Move from expression patterns to the recurring, sex/APOE-linked KDA candidates.",
    "Transition: Move from expression patterns to recurring, sex/APOE-linked genes returned from KDA calls.",
  ],
  ["Sex/APOE-linked KDA findings: recurring candidates", "Recurring sex/APOE-linked genes from KDA calls"],
  ["Candidate and mitochondrial connection", "Gene and mitochondrial connection"],
  [
    "These candidates recur across multiple sex/APOE groups or connect a repeated mitochondrial theme to network genes.",
    "These genes recur among KDA calls from multiple sex/APOE groups or connect a repeated mitochondrial theme to network genes.",
  ],
  [
    "These are KDA hypotheses: network proximity nominates candidates but does not establish causal regulation.",
    "Genes returned from KDA calls are hypotheses: network proximity does not establish causal regulation.",
  ],
  [
    "Teaching goal: Summarize the recurring sex/APOE-linked KDA candidates without mixing them with DEG-only results.",
    "Teaching goal: Summarize recurring sex/APOE-linked genes returned from KDA calls without mixing them with DEG-only results.",
  ],
  [
    "Boundary: KDA identifies network neighborhoods, not direct regulation or causality. Recurrence across separately analyzed groups is descriptive rather than independent replication.",
    "Boundary: A KDA call identifies a network neighborhood, not direct regulation or causality. Recurrence across separately analyzed groups is descriptive rather than independent replication.",
  ],
  [
    "Transition: Review the more qualified or secondary sex/APOE-linked KDA leads.",
    "Transition: Review the more qualified or secondary genes returned from sex/APOE-linked KDA calls.",
  ],
  ["Sex/APOE-linked KDA findings: qualified and secondary leads", "Qualified sex/APOE-linked genes from KDA calls"],
  ["Candidate and main qualification", "Gene and main qualification"],
  [
    "PLCG2 has strong AD genetics, but its exact KDA neighborhood contains MT-CO1 alone.",
    "PLCG2 has strong AD genetics, but the network neighborhood underlying its KDA calls contains MT-CO1 alone.",
  ],
  [
    "Finding 18 is a secondary KDA lead from the completed Phase 19b genetic-support analysis.",
    "Finding 18 is a secondary gene returned from a KDA call and supported by the completed Phase 19b genetic-support analysis.",
  ],
  [
    "INTS8 is a one-call inhibitory-neuron lead; human genetics supports follow-up, but network recurrence is absent.",
    "INTS8 was returned from one inhibitory-neuron KDA call; human genetics supports follow-up, but network recurrence is absent.",
  ],
  [
    "Teaching goal: Keep promising but qualified KDA findings visible without giving them the same weight as broader recurring results.",
    "Teaching goal: Keep promising but qualified genes returned from KDA calls visible without giving them the same weight as broader recurring results.",
  ],
  [
    "Walk through: PLCG2 has strong gene-level genetics but a fragile one-gene mitochondrial neighborhood. APOE is biologically important but context-dependent. The female ε4 vascular module is small. INTS8 is a singleton male ε2 inhibitory-neuron KDA lead strengthened by gene-level human genetics.",
    "Walk through: PLCG2 has strong gene-level genetics but a fragile one-gene mitochondrial neighborhood. APOE is biologically important but context-dependent. The female ε4 vascular module is small. INTS8 is returned from one male ε2 inhibitory-neuron KDA call and is strengthened by gene-level human genetics.",
  ],
  [
    "Boundary: Gene-level genetics does not validate the inferred cell type, sex/APOE context, or KDA neighborhood.",
    "Boundary: Gene-level genetics does not validate the inferred cell type, sex/APOE context, or network neighborhood underlying a KDA call.",
  ],
  ["Shared KDA mechanism", "Shared result from KDA calls"],
  [
    "ROSMAP and SEA-AD agree more on mitochondrial gene sets than on exact KDA candidates.",
    "ROSMAP and SEA-AD agree more on mitochondrial gene sets than on exact genes returned from KDA calls.",
  ],
  [
    "Presentation priority: Findings 1–6 first, sex/APOE-linked KDA findings second, and Findings 7, 10, and 17 last.",
    "Presentation priority: Findings 1–6 first, sex/APOE-linked results from KDA calls second, and Findings 7, 10, and 17 last.",
  ],
]);

const targetParts = [156, 157, 158, 159, 160].flatMap((number) => [
  `ppt/slides/slide${number}.xml`,
  `ppt/notesSlides/notesSlide${number}.xml`,
]);

const { importRuntimeModule } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href
);
const JSZipModule = await importRuntimeModule("jszip");
const JSZip = JSZipModule.default ?? JSZipModule;
const zip = await JSZip.loadAsync(await fs.readFile(SOURCE));
const counts = new Map([...replacements.keys()].map((text) => [text, 0]));
const orderedReplacements = [...replacements].sort((a, b) => b[0].length - a[0].length);

for (const partName of targetParts) {
  const part = zip.file(partName);
  if (!part) throw new Error(`Missing package part: ${partName}`);
  let xml = await part.async("string");
  for (const [before, after] of orderedReplacements) {
    const matches = xml.split(before).length - 1;
    if (matches > 0) {
      xml = xml.split(before).join(after);
      counts.set(before, counts.get(before) + matches);
    }
  }
  zip.file(partName, xml);
}

for (const [before, count] of counts) {
  if (count === 0) throw new Error(`Expected terminology was not found: ${before}`);
}

await fs.mkdir(path.dirname(OUTPUT), { recursive: true });
await fs.writeFile(
  OUTPUT,
  await zip.generateAsync({
    type: "nodebuffer",
    compression: "DEFLATE",
    compressionOptions: { level: 6 },
  }),
);

console.log(JSON.stringify({ source: SOURCE, output: OUTPUT, replacements: Object.fromEntries(counts) }, null, 2));
