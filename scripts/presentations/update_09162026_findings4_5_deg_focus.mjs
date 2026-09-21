#!/usr/bin/env node

/** Refocus Findings 4 and 5 on DEG direction and remove their limitation slides. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const SKILL_DIR =
  "/Users/rzhuang/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations";
const WORKSPACE_DIR = "/Users/rzhuang/Documents/VscodeProjects/alzheimer";
const SOURCE = path.join(
  WORKSPACE_DIR,
  "docs/presentations/09162026/09162026_sex_apoe_kda_fine_broad_slide58_notes_refreshed_20260920_v2.pptx",
);
const RESULT_DIR = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_findings4_5_deg_focus_target_20260920",
);
const BUILD_DIR = path.join(RESULT_DIR, "build");
const FINAL_PPTX = path.join(
  RESULT_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_slide58_notes_refreshed_findings4_5_deg_focus_20260920.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "95f7568e504cea66174399dd44142e005aa6e1c4817e819c462d9180c1a4a3bd";
const SOURCE_SLIDE_COUNT = 159;
const FINAL_SLIDE_COUNT = 157;
const REMOVED_SOURCE_SLIDES = [67, 74];

const TEXT_UPDATES = [
  {
    slide: 62,
    name: "TextBox 4",
    text: "Finding based on DEG directions across fine-cell comparisons.",
  },
  {
    slide: 63,
    name: "TextBox 24",
    text: "The finding is specific to fine-cell DEG occurrences because direct broad-cell results disagree.",
  },
  { slide: 64, name: "TextBox 12", text: "95%" },
  {
    slide: 64,
    name: "TextBox 13",
    text: "nuclear-encoded OXPHOS occurrences",
  },
  {
    slide: 64,
    name: "TextBox 14",
    text: "AD-down across fine-cell comparisons",
  },
  {
    slide: 64,
    name: "TextBox 18",
    text: "206 AD-down and 10 AD-up occurrences",
  },
  {
    slide: 64,
    name: "TextBox 22",
    text: "38 AD-down and 26 AD-up occurrences",
  },
  { slide: 64, name: "TextBox 24", text: "Main DEG pattern" },
  { slide: 64, name: "TextBox 25", text: "Nuclear-encoded decrease" },
  {
    slide: 64,
    name: "TextBox 26",
    text: "The clearest pattern is lower nuclear-encoded OXPHOS expression across female ε4 fine-cell comparisons.",
  },
  {
    slide: 69,
    name: "TextBox 4",
    text: "Finding based on DEG directions across fine-cell comparisons.",
  },
  {
    slide: 69,
    name: "TextBox 20",
    text: "Both OXPHOS gene sets show lower expression across fine-cell DEG occurrences.",
  },
  {
    slide: 71,
    name: "TextBox 2",
    text: "Fine-cell DEG occurrences and direct broad-cell sensitivity point mainly downward.",
  },
  { slide: 71, name: "TextBox 12", text: "523" },
  {
    slide: 71,
    name: "TextBox 13",
    text: "AD-down OXPHOS occurrences",
  },
  {
    slide: 71,
    name: "TextBox 14",
    text: "119 core MT + 404 nuclear-encoded",
  },
  {
    slide: 71,
    name: "TextBox 18",
    text: "119 AD-down and 13 AD-up occurrences",
  },
  {
    slide: 71,
    name: "TextBox 22",
    text: "404 AD-down and 63 AD-up occurrences",
  },
  { slide: 71, name: "TextBox 24", text: "Overall DEG direction" },
  { slide: 71, name: "TextBox 25", text: "Both gene sets down" },
  {
    slide: 71,
    name: "TextBox 26",
    text: "Core MT and nuclear-encoded OXPHOS occurrences are predominantly AD-down.",
  },
  {
    slide: 72,
    name: "TextBox 1",
    text: "Male ε2 has unusually large MitoCarta MT DEG sets",
  },
  {
    slide: 72,
    name: "TextBox 2",
    text: "The DEG-set size matters when comparing how many genes are returned from KDA calls.",
  },
  { slide: 72, name: "TextBox 5", text: "85 MitoCarta MT DEGs" },
  {
    slide: 72,
    name: "TextBox 8",
    text: "ALL ELIGIBLE FINE-CELL COMPARISONS",
  },
  { slide: 72, name: "TextBox 9", text: "16.5 MitoCarta MT DEGs" },
  {
    slide: 72,
    name: "TextBox 16",
    text: "More DEGs provide more opportunities for a gene to be returned from a KDA call. This does not change the DEG direction counts on the preceding slide.",
  },
  { slide: 73, name: "TextBox 12", text: "DEG INTERPRETATION" },
  { slide: 73, name: "TextBox 13", text: "Direction, not function" },
  {
    slide: 73,
    name: "TextBox 14",
    text: "Lower gene expression does not by itself show lower respiration, ATP production, or mitochondrial fitness.",
  },
  {
    slide: 73,
    name: "TextBox 17",
    text: "The coordinated DEG decrease is biologically interesting and needs protein or functional follow-up.",
  },
];

function notes({ goal, walkthrough, boundary, transition, sources }) {
  return [
    `Teaching goal: ${goal}`,
    "",
    `Walk through: ${walkthrough}`,
    "",
    `Scientific boundary: ${boundary}`,
    "",
    `Transition: ${transition}`,
    ...(sources ? ["", `Sources: ${sources}`] : []),
  ].join("\n");
}

const ANALYSIS_SOURCE =
  "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md";

const NOTES_BY_SOURCE_SLIDE = new Map([
  [
    58,
    notes({
      goal: "Quantify the ROSMAP DEG-occurrence pattern for Finding 3.",
      walkthrough:
        "Across eligible female APOE ε2 fine-cell comparisons used for KDA, core MT genes contribute 128 DEG occurrences: 127 AD-up and one AD-down, so 99 percent are upregulated. Nuclear-encoded OXPHOS genes contribute 243 DEG occurrences: 239 AD-up and four AD-down, so 98 percent are upregulated. One occurrence means that one gene is a DEG in one eligible fine-cell comparison; the same gene can contribute another occurrence in another comparison.",
      boundary:
        "The numbers 128 and 243 are gene-by-comparison occurrences, not counts of unique genes, cells, donors, or genes returned from KDA calls. The percentages do not measure expression magnitude, OXPHOS protein abundance, respiration, or ATP production.",
      transition:
        "Compare this primary fine-cell DEG pattern with the direct broad-cell ROSMAP result and the available SEA-AD coverage.",
      sources: `${ANALYSIS_SOURCE}, Finding 3 and Section 2.2.`,
    }),
  ],
  [
    62,
    notes({
      goal: "Introduce Finding 4 as a female APOE ε4 DEG-direction result.",
      walkthrough:
        "The primary signal is lower expression of nuclear-encoded OXPHOS genes across female APOE ε4 fine-cell comparisons. Core MT genes are less consistently directional. The next slides quantify those DEG occurrences, test whether the pattern survives broad-cell aggregation, and explain why the resolution difference matters.",
      boundary:
        "This finding describes differential gene expression. It does not directly measure respiratory-complex proteins, oxygen consumption, ATP production, or a causal sex-by-APOE interaction.",
      transition: "State the two OXPHOS gene-set directions in plain language.",
      sources: `${ANALYSIS_SOURCE}, Finding 4.`,
    }),
  ],
  [
    63,
    notes({
      goal: "Explain the female APOE ε4 pattern before showing the counts.",
      walkthrough:
        "Nuclear-encoded OXPHOS genes provide the clear signal: 206 of 216 repeated DEG occurrences are lower in AD. Core MT genes are mixed, with 38 AD-down and 26 AD-up occurrences. Therefore the result is a nuclear-encoded OXPHOS decrease, not a uniform decrease across all MitoCarta MT genes.",
      boundary:
        "An occurrence is one gene observed as a DEG in one fine-cell comparison. Repeated occurrences are not independent donors or unique genes, and the direct broad-cell result points in the opposite direction.",
      transition: "Show the exact occurrence counts and percentages.",
      sources: `${ANALYSIS_SOURCE}, Finding 4 and Section 2.2.`,
    }),
  ],
  [
    64,
    notes({
      goal: "Quantify the female APOE ε4 DEG directions without mixing them with pathway statistics.",
      walkthrough:
        "Across eligible fine-cell comparisons, nuclear-encoded OXPHOS genes contribute 216 DEG occurrences: 206 AD-down and 10 AD-up. Thus 95 percent are downregulated. Core MT genes contribute 64 occurrences: 38 AD-down and 26 AD-up, or 59 percent downregulated. The nuclear-encoded component is both larger and much more consistently downward.",
      boundary:
        "These are repeated gene-by-fine-cell DEG occurrences. They are not counts of unique genes, cells, donors, or genes returned from KDA calls, and they do not quantify the magnitude of expression change.",
      transition: "Check whether direct broad-cell analysis supports the same direction.",
      sources: `${ANALYSIS_SOURCE}, Finding 4 and Section 2.2.`,
    }),
  ],
  [
    65,
    notes({
      goal: "Show that the female APOE ε4 result changes with cell-type resolution.",
      walkthrough:
        "The fine-cell DEG result points strongly downward for nuclear-encoded OXPHOS genes. In direct broad-cell analysis, however, the ROSMAP excitatory-neuron score is weakly positive and not significant, while the SEA-AD excitatory-neuron score is significantly positive. The available SEA-AD fine-cell check is only one small astrocyte comparison and does not provide convincing support.",
      boundary:
        "The disagreement does not invalidate the fine-cell observation, but it prevents describing the decrease as a broad-cell-wide or cross-cohort effect. Aggregation, subtype composition, and limited matched coverage remain plausible explanations.",
      transition: "Explain the biological importance and the resolution warning together.",
      sources: `${ANALYSIS_SOURCE}, Finding 4 and validation sections.`,
    }),
  ],
  [
    66,
    notes({
      goal: "Explain why a nuclear-encoded OXPHOS decrease could matter biologically.",
      walkthrough:
        "Most respiratory-complex subunits are encoded by nuclear DNA. Lower expression across many of these genes could reduce the supply of complex components or reflect a stress-associated cell state. APOE ε4 makes the hypothesis important because it strongly increases late-onset Alzheimer’s disease risk at the population level.",
      boundary:
        "Gene expression alone cannot establish lower respiratory capacity, and the broad-cell direction reverses. The most cautious interpretation is a fine-cell signal that warrants targeted follow-up.",
      transition: "Place the result in prior research and summarize its evidence level.",
      sources: `${ANALYSIS_SOURCE}, Finding 4.`,
    }),
  ],
  [
    68,
    notes({
      goal: "Place Finding 4 in prior research without overstating replication.",
      walkthrough:
        "The cited APOE4 studies support the biological plausibility of altered mitochondrial homeostasis, and cell-resolved Alzheimer’s studies support strong heterogeneity among brain cell states. None reproduces the exact female APOE ε4 nuclear-encoded OXPHOS DEG pattern shown here.",
      boundary:
        "Biological plausibility, novelty, and replication are separate judgments. The current finding remains resolution-sensitive and needs independent confirmation.",
      transition: "Move to the coordinated downward pattern in male APOE ε2 cells.",
      sources: `${ANALYSIS_SOURCE}, Finding 4 literature context.`,
    }),
  ],
  [
    69,
    notes({
      goal: "Introduce Finding 5 as a coordinated male APOE ε2 DEG decrease.",
      walkthrough:
        "Unlike Finding 4, both defined OXPHOS gene sets move downward in male APOE ε2 fine-cell comparisons. Core MT genes are predominantly AD-down, and nuclear-encoded OXPHOS genes are also predominantly AD-down. The next slides quantify the repeated DEG occurrences and show why the unusually large MitoCarta MT DEG sets matter for interpreting later KDA output.",
      boundary:
        "The result describes disease-associated gene expression in observed tissue. It does not imply that APOE ε2 causes the decrease or that lower expression explains APOE ε2 population-level protection.",
      transition: "State the coordinated direction and its contrast with male APOE ε3/ε3.",
      sources: `${ANALYSIS_SOURCE}, Finding 5.`,
    }),
  ],
  [
    70,
    notes({
      goal: "Explain the coordinated male APOE ε2 decrease in plain language.",
      walkthrough:
        "Core MT genes contribute 132 DEG occurrences, of which 119 are lower in AD. Nuclear-encoded OXPHOS genes contribute 467 occurrences, of which 404 are lower in AD. Both gene sets therefore point downward, unlike the opposite-direction pattern seen in male APOE ε3 homozygous cells.",
      boundary:
        "APOE ε2 lowers average Alzheimer’s disease risk at the population level, but that does not predict every molecular state after disease develops. The observed expression pattern is descriptive rather than causal.",
      transition: "Show the exact DEG-occurrence percentages.",
      sources: `${ANALYSIS_SOURCE}, Finding 5 and Section 2.2.`,
    }),
  ],
  [
    71,
    notes({
      goal: "Quantify the male APOE ε2 DEG burden in both OXPHOS gene sets.",
      walkthrough:
        "Across eligible fine-cell comparisons, core MT genes contribute 132 DEG occurrences: 119 AD-down and 13 AD-up, so 90 percent are downregulated. Nuclear-encoded OXPHOS genes contribute 467 occurrences: 404 AD-down and 63 AD-up, so 87 percent are downregulated. Together, 523 OXPHOS occurrences are AD-down.",
      boundary:
        "The 523 value combines repeated gene-by-fine-cell occurrences from two defined gene sets. It is not a count of unique genes, donors, cells, or genes returned from KDA calls, and it does not measure expression magnitude or mitochondrial function.",
      transition: "Explain why the male APOE ε2 DEG sets are unusually large.",
      sources: `${ANALYSIS_SOURCE}, Finding 5 and Section 2.2.`,
    }),
  ],
  [
    72,
    notes({
      goal: "Define the DEG-set-size caveat for male APOE ε2.",
      walkthrough:
        "For each fine-cell comparison, significant DEGs are restricted to MitoCarta MT genes and to genes available in the relevant network before making the KDA call. The median male APOE ε2 set contains 85 such DEGs, compared with 16.5 across all eligible fine-cell comparisons. More input DEGs create more opportunities for a gene to be returned from a KDA call.",
      boundary:
        "This size difference affects comparisons of KDA output counts. It does not change the observed AD-up versus AD-down DEG occurrence counts on the preceding slide. SEA-AD has no matching active male APOE ε2 category here.",
      transition: "Return to the biological meaning of the coordinated DEG direction.",
      sources: `${ANALYSIS_SOURCE}, Finding 5 and KDA query-size diagnostics.`,
    }),
  ],
  [
    73,
    notes({
      goal: "Separate the male APOE ε2 DEG direction from inherited-risk interpretation and mitochondrial function.",
      walkthrough:
        "APOE ε2 lowers average Alzheimer’s disease risk, but diseased male APOE ε2 tissue can still show lower expression of both OXPHOS gene sets. Possible explanations include respiratory reduction, altered cell state, or selective survival of particular cells. The DEG result identifies a biological pattern to test, not its mechanism.",
      boundary:
        "Lower gene expression does not by itself demonstrate lower respiratory-complex abundance, respiration, ATP production, or mitochondrial fitness. Protein and functional measurements are needed.",
      transition: "Place the result in prior research and summarize its evidence level.",
      sources: `${ANALYSIS_SOURCE}, Finding 5.`,
    }),
  ],
  [
    75,
    notes({
      goal: "Place Finding 5 in prior research without overstating independent support.",
      walkthrough:
        "Population genetics establishes the average protective association of APOE ε2. Sex-specific network and cell-resolved Alzheimer’s studies support the need to examine molecular responses within sex, genotype, and cell context. None independently reproduces this exact male APOE ε2 coordinated OXPHOS decrease.",
      boundary:
        "The finding is potentially novel but currently lacks a matched SEA-AD category and functional validation. Novelty and evidence strength should remain separate.",
      transition: "Move to Finding 6, where male APOE ε4 shows opposite directions across the two OXPHOS gene sets.",
      sources: `${ANALYSIS_SOURCE}, Finding 5 literature context.`,
    }),
  ],
]);

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

function relationshipTags(xml) {
  return [...xml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map((match) => match[0]);
}

function relationshipAttribute(tag, name) {
  return tag.match(new RegExp(`\\b${name}="([^"]+)"`))?.[1];
}

function relationshipPartPath(ownerPartPath) {
  return path.posix.join(
    path.posix.dirname(ownerPartPath),
    "_rels",
    `${path.posix.basename(ownerPartPath)}.rels`,
  );
}

async function relatedPartPath(zip, ownerPartPath, relationshipTypeSuffix) {
  const relsPath = relationshipPartPath(ownerPartPath);
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing ${relsPath}`);
  for (const tag of relationshipTags(relsXml)) {
    const type = relationshipAttribute(tag, "Type");
    if (!type?.endsWith(`/relationships/${relationshipTypeSuffix}`)) continue;
    const target = relationshipAttribute(tag, "Target");
    if (!target) continue;
    if (target.startsWith("/")) return target.slice(1);
    return path.posix.normalize(path.posix.join(path.posix.dirname(ownerPartPath), target));
  }
  throw new Error(`${ownerPartPath} lacks a ${relationshipTypeSuffix} relationship`);
}

async function visibleSlidePart(zip, ordinal) {
  const presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  const presentationRelsXml = await zip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  if (!presentationXml || !presentationRelsXml) {
    throw new Error("Presentation ordering metadata is missing");
  }
  const slideIds = [...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g)]
    .map((match) => match[1]);
  const relationshipId = slideIds[ordinal - 1];
  if (!relationshipId) throw new Error(`Visible slide ${ordinal} was not found`);
  const relation = relationshipTags(presentationRelsXml).find(
    (tag) =>
      relationshipAttribute(tag, "Id") === relationshipId &&
      relationshipAttribute(tag, "Type")?.endsWith("/slide"),
  );
  const target = relation && relationshipAttribute(relation, "Target");
  if (!target) throw new Error(`Slide relationship ${relationshipId} was not found`);
  return target.startsWith("/")
    ? target.slice(1)
    : path.posix.normalize(path.posix.join("ppt", target));
}

function removeContentTypeOverride(contentTypesXml, partPath) {
  const partName = `/${partPath}`;
  const target = [...contentTypesXml.matchAll(/<Override\b[^>]*\/?\s*>/g)]
    .map((match) => match[0])
    .find((tag) => relationshipAttribute(tag, "PartName") === partName);
  if (!target) throw new Error(`Missing content-type override for ${partName}`);
  return contentTypesXml.replace(target, "");
}

function updateAppProperties(appXml) {
  let updated = appXml
    .replace(/<Slides>159<\/Slides>/, "<Slides>157</Slides>")
    .replace(/<Notes>159<\/Notes>/, "<Notes>157</Notes>")
    .replace(
      /(<vt:lpstr>Slide Titles<\/vt:lpstr>\s*<\/vt:variant>\s*<vt:variant>\s*<vt:i4>)159(<\/vt:i4>)/,
      "$1157$2",
    );

  const titlesMatch = updated.match(
    /(<TitlesOfParts>\s*<vt:vector size=")162(" baseType="lpstr">)([\s\S]*?)(<\/vt:vector>\s*<\/TitlesOfParts>)/,
  );
  if (!titlesMatch) throw new Error("Could not locate TitlesOfParts metadata");
  let entriesXml = titlesMatch[3];
  const entries = [...entriesXml.matchAll(/<vt:lpstr>[\s\S]*?<\/vt:lpstr>/g)];
  if (entries.length !== 162) {
    throw new Error(`Expected 162 TitlesOfParts entries, found ${entries.length}`);
  }
  for (const entryIndex of [76, 69]) {
    const entry = entries[entryIndex];
    entriesXml =
      entriesXml.slice(0, entry.index) + entriesXml.slice(entry.index + entry[0].length);
  }
  updated = updated.replace(
    titlesMatch[0],
    `${titlesMatch[1]}160${titlesMatch[2]}${entriesXml}${titlesMatch[4]}`,
  );
  return updated;
}

function finalSlideNumber(sourceSlideNumber) {
  return sourceSlideNumber - REMOVED_SOURCE_SLIDES.filter((n) => n < sourceSlideNumber).length;
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
  if (sourceHash !== EXPECTED_SOURCE_SHA256) {
    throw new Error(`Source deck changed before the edit: ${sourceHash}`);
  }

  const { importRuntimeModule } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href
  );
  const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");
  const JSZipModule = await importRuntimeModule("jszip");
  const JSZip = JSZipModule.default ?? JSZipModule;

  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const slides = slidesFromPresentation(presentation);
  if (slides.length !== SOURCE_SLIDE_COUNT) {
    throw new Error(`Expected ${SOURCE_SLIDE_COUNT} slides, found ${slides.length}`);
  }

  const snapshot = await presentation.inspect({
    kind: "textbox",
    include: "id,slide,name,text,bbox",
    maxChars: 4000000,
  });
  const records = parseNdjson(snapshot.ndjson).filter(
    (record) => record.kind === "textbox" && typeof record.text === "string",
  );

  const visibleSourceSlides = [...new Set(TEXT_UPDATES.map((update) => update.slide))];
  const beforePngs = new Map();
  for (const slideNumber of visibleSourceSlides) {
    const png = await blobBuffer(
      await presentation.export({ slide: slides[slideNumber - 1], format: "png", scale: 1.5 }),
    );
    beforePngs.set(slideNumber, png);
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-before.png`), png);
  }

  for (const update of TEXT_UPDATES) {
    const matches = records.filter(
      (record) => record.slide === update.slide && record.name === update.name,
    );
    if (matches.length !== 1) {
      throw new Error(
        `Expected one ${update.name} on slide ${update.slide}, found ${matches.length}`,
      );
    }
    presentation.resolve(matches[0].id).text = update.text;
  }
  for (const [slideNumber, updatedNotes] of NOTES_BY_SOURCE_SLIDE) {
    slides[slideNumber - 1].speakerNotes.textFrame.setText(updatedNotes);
    slides[slideNumber - 1].speakerNotes.setVisible(true);
  }

  for (const slideNumber of visibleSourceSlides) {
    const png = await blobBuffer(
      await presentation.export({ slide: slides[slideNumber - 1], format: "png", scale: 1.5 }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-after.png`), png);
    if (sha256(beforePngs.get(slideNumber)) === sha256(png)) {
      throw new Error(`Visible slide ${slideNumber} did not change`);
    }
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed during the edit");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  for (const slideNumber of visibleSourceSlides) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const revisedSlideXml = await artifactZip.file(artifactSlidePart)?.async("string");
    if (!revisedSlideXml) throw new Error(`Missing revised slide XML for slide ${slideNumber}`);
    sourceZip.file(sourceSlidePart, revisedSlideXml);
  }
  for (const slideNumber of NOTES_BY_SOURCE_SLIDE.keys()) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const sourceNotesPart = await relatedPartPath(sourceZip, sourceSlidePart, "notesSlide");
    const artifactNotesPart = await relatedPartPath(artifactZip, artifactSlidePart, "notesSlide");
    const revisedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!revisedNotesXml) throw new Error(`Missing revised notes XML for slide ${slideNumber}`);
    sourceZip.file(sourceNotesPart, revisedNotesXml);
  }

  const presentationPath = "ppt/presentation.xml";
  const presentationRelsPath = "ppt/_rels/presentation.xml.rels";
  let presentationXml = await sourceZip.file(presentationPath)?.async("string");
  let presentationRelsXml = await sourceZip.file(presentationRelsPath)?.async("string");
  let contentTypesXml = await sourceZip.file("[Content_Types].xml")?.async("string");
  const appXml = await sourceZip.file("docProps/app.xml")?.async("string");
  if (!presentationXml || !presentationRelsXml || !contentTypesXml || !appXml) {
    throw new Error("The source PPTX is missing required package parts");
  }

  const slideIdTags = [...presentationXml.matchAll(/<p:sldId\b[^>]*\/?\s*>/g)]
    .map((match) => match[0]);
  if (slideIdTags.length !== SOURCE_SLIDE_COUNT) {
    throw new Error(`Expected ${SOURCE_SLIDE_COUNT} slide IDs, found ${slideIdTags.length}`);
  }
  const presentationRelationships = relationshipTags(presentationRelsXml);
  for (const slideNumber of [...REMOVED_SOURCE_SLIDES].sort((a, b) => b - a)) {
    const slideIdTag = slideIdTags[slideNumber - 1];
    const relationshipId = relationshipAttribute(slideIdTag, "r:id");
    const relationshipTag = presentationRelationships.find(
      (tag) => relationshipAttribute(tag, "Id") === relationshipId,
    );
    const target = relationshipTag && relationshipAttribute(relationshipTag, "Target");
    if (!relationshipTag || !target) {
      throw new Error(`Could not resolve slide ${slideNumber} relationship`);
    }
    const slidePartPath = target.startsWith("/")
      ? target.slice(1)
      : path.posix.normalize(path.posix.join("ppt", target));
    const slideRelsPath = relationshipPartPath(slidePartPath);
    const notesPartPath = await relatedPartPath(sourceZip, slidePartPath, "notesSlide");
    const notesRelsPath = relationshipPartPath(notesPartPath);

    sourceZip.remove(slidePartPath);
    sourceZip.remove(slideRelsPath);
    sourceZip.remove(notesPartPath);
    sourceZip.remove(notesRelsPath);
    contentTypesXml = removeContentTypeOverride(contentTypesXml, slidePartPath);
    contentTypesXml = removeContentTypeOverride(contentTypesXml, notesPartPath);
    presentationXml = presentationXml.replace(slideIdTag, "");
    presentationRelsXml = presentationRelsXml.replace(relationshipTag, "");
  }

  sourceZip.file(presentationPath, presentationXml);
  sourceZip.file(presentationRelsPath, presentationRelsXml);
  sourceZip.file("[Content_Types].xml", contentTypesXml);
  sourceZip.file("docProps/app.xml", updateAppProperties(appXml));

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
    await sourceZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const validation = await finalizePresentation({
    explicitTotalSlideCount: FINAL_SLIDE_COUNT,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [14],
    requiredEmbeddedWorkbookChartOwnerSlides: [14],
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
    receiptPath: path.join(BUILD_DIR, "findings4_5_deg_focus.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalSlides = slidesFromPresentation(reopened);
  if (finalSlides.length !== FINAL_SLIDE_COUNT) {
    throw new Error(`Final deck has ${finalSlides.length} slides, expected ${FINAL_SLIDE_COUNT}`);
  }
  const finalSnapshot = await reopened.inspect({
    kind: "slide,textbox,notes,chart,layout",
    maxChars: 6000000,
  });
  await fs.writeFile(path.join(BUILD_DIR, "final.inspect.ndjson"), finalSnapshot.ndjson, "utf8");
  const finalRecords = parseNdjson(finalSnapshot.ndjson);

  for (const update of TEXT_UPDATES) {
    const finalSlide = finalSlideNumber(update.slide);
    const match = finalRecords.find(
      (record) =>
        record.kind === "textbox" &&
        record.slide === finalSlide &&
        record.name === update.name &&
        record.text === update.text,
    );
    if (!match) {
      throw new Error(`Final text validation failed for slide ${finalSlide} ${update.name}`);
    }
  }
  for (const [sourceSlideNumber, expectedNotes] of NOTES_BY_SOURCE_SLIDE) {
    const finalSlide = finalSlideNumber(sourceSlideNumber);
    const record = finalRecords.find(
      (item) => item.kind === "notes" && item.slide === finalSlide,
    );
    if (record?.text?.trim() !== expectedNotes.trim()) {
      throw new Error(`Final notes validation failed for slide ${finalSlide}`);
    }
  }
  const findingRangeText = finalRecords
    .filter(
      (record) =>
        record.kind === "textbox" && record.slide >= 62 && record.slide <= 73,
    )
    .map((record) => record.text || "")
    .join("\n");
  if (/enrich/i.test(findingRangeText)) {
    throw new Error("Findings 4-5 still contain visible enrichment language");
  }
  if (
    findingRangeText.includes("What Finding 4 does not prove") ||
    findingRangeText.includes("What Finding 5 does not prove")
  ) {
    throw new Error("A requested limitation slide remains in the final deck");
  }

  for (const finalSlideNumberToRender of [62, 63, 64, 68, 70, 71, 72, 73]) {
    const png = await blobBuffer(
      await reopened.export({
        slide: finalSlides[finalSlideNumberToRender - 1],
        format: "png",
        scale: 1.5,
      }),
    );
    await fs.writeFile(
      path.join(BUILD_DIR, `slide-${finalSlideNumberToRender}-final.png`),
      png,
    );
  }

  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed before installation");
  }
  await fs.copyFile(FINAL_PPTX, SOURCE);

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        previousSourceSha256: sourceHash,
        installedSourceSha256: sha256(await fs.readFile(SOURCE)),
        output: FINAL_PPTX,
        removedSourceSlides: REMOVED_SOURCE_SLIDES,
        finalSlideCount: FINAL_SLIDE_COUNT,
        updatedSourceSlides: visibleSourceSlides,
        updatedNotesSourceSlides: [...NOTES_BY_SOURCE_SLIDE.keys()],
        validation,
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exitCode = 1;
});
