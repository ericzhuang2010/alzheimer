#!/usr/bin/env node

/** Add the secondary female ε3/ε3 nuclear-OXPHOS result to Finding 1. */

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
  "results/presentations/09162026_finding1_nuclear_oxphos/build_v2",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_finding1_nuclear_oxphos/output/09162026_sex_apoe_kda_fine_broad_finding1_nuclear_oxphos_20260919_v2.pptx",
);
const EXPECTED_SLIDES = 160;
const VISIBLE_SLIDES = [42, 43, 44, 45, 46];

const TEXT_UPDATES = [
  {
    slide: 42,
    name: "TextBox 3",
    text: "Female APOE ε3/ε3 cells show a strong mtDNA-led OXPHOS increase",
  },
  {
    slide: 42,
    name: "TextBox 4",
    text: "A mitochondrial DEG finding with secondary nuclear-OXPHOS support in ROSMAP.",
  },
  {
    slide: 42,
    name: "TextBox 20",
    text: "SEA-AD supports the mtDNA pattern. Nuclear-OXPHOS support is currently ROSMAP-only.",
  },
  {
    slide: 43,
    name: "TextBox 2",
    text: "The mtDNA result repeats across ROSMAP fine-cell comparisons and receives support from SEA-AD.",
  },
  {
    slide: 43,
    name: "TextBox 19",
    text: "Nuclear OXPHOS RNA also mostly rises in ROSMAP, but cross-cohort support is strongest for mtDNA OXPHOS.",
  },
  {
    slide: 44,
    name: "TextBox 1",
    text: "ROSMAP: female ε3/ε3 OXPHOS signals are predominantly AD-up",
  },
  {
    slide: 44,
    name: "TextBox 5",
    text: "mtDNA OXPHOS\n217/217 AD-up, 29 input queries enriched",
    position: { left: 103.68, top: 270.72, width: 519.36, height: 82.56 },
  },
  {
    slide: 44,
    name: "TextBox 6",
    text: "Nuclear OXPHOS\n76/89 AD-up (85%), 4 input queries enriched",
    position: { left: 657.6, top: 270.72, width: 514.56, height: 82.56 },
  },
  {
    slide: 45,
    name: "TextBox 1",
    text: "SEA-AD adds strong support for the excitatory-neuron mtDNA OXPHOS pattern",
  },
  {
    slide: 45,
    name: "TextBox 35",
    text: "Every shared gene is upregulated in both datasets.",
  },
  {
    slide: 46,
    name: "TextBox 17",
    text: "mtDNA OXPHOS rises in ROSMAP and SEA-AD. Nuclear OXPHOS also mostly rises in ROSMAP.",
  },
];

function notes({ goal, walkthrough, boundary, transition }) {
  return [
    `Teaching goal: ${goal}`,
    "",
    `Walk through: ${walkthrough}`,
    "",
    `Scientific boundary: ${boundary}`,
    "",
    `Transition: ${transition}`,
  ].join("\n");
}

const NOTES_BY_SLIDE = new Map([
  [
    42,
    notes({
      goal:
        "Introduce Finding 1 as a strong mtDNA-OXPHOS increase with secondary nuclear-OXPHOS support in ROSMAP.",
      walkthrough:
        "Finding 1 concerns female APOE epsilon-3 homozygous cells, with the clearest cross-cohort evidence in excitatory neurons. The primary result is a repeated increase in mitochondrial-DNA-encoded OXPHOS RNA. Nuclear-encoded OXPHOS genes also mostly increase in ROSMAP, but this component is less consistently enriched and lacks the same SEA-AD support.",
      boundary:
        "The evidence does not establish increased ATP production, a causal regulator, or a disease-by-sex-by-APOE interaction. The nuclear-OXPHOS observation is secondary ROSMAP evidence rather than a replicated cross-cohort conclusion.",
      transition: "State the primary mtDNA result and the secondary nuclear result in plain language.",
    }),
  ],
  [
    43,
    notes({
      goal: "Explain the primary and secondary parts of Finding 1 in plain language.",
      walkthrough:
        "Read the four labels first: female, APOE epsilon-3 homozygous, excitatory neurons, and Alzheimer’s disease. Mitochondrial DNA encodes 13 protein subunits of oxidative phosphorylation, or OXPHOS. RNA from those genes is more abundant in AD than in the comparison group. Nuclear OXPHOS RNA also mostly rises in ROSMAP, but the strongest repeated and cross-cohort evidence concerns the mitochondrial-DNA-encoded genes.",
      boundary:
        "Higher RNA abundance does not demonstrate more OXPHOS protein, greater respiration, increased ATP production, or healthier mitochondria. It also does not establish that the disease response differs statistically by sex or APOE genotype.",
      transition: "Show the ROSMAP evidence for both OXPHOS gene sets.",
    }),
  ],
  [
    44,
    notes({
      goal:
        "Present the primary mtDNA-OXPHOS result and the secondary nuclear-OXPHOS result in ROSMAP.",
      walkthrough:
        "F_e33 denotes the female APOE epsilon-3 homozygous group. Across eligible fine-cell DEG queries, mtDNA OXPHOS genes contribute 217 occurrences, and all 217 are upregulated in AD. Twenty-nine mtDNA input queries are enriched. Nuclear OXPHOS contributes 89 occurrences, with 76 upregulated and 13 downregulated, so 85 percent are upregulated. Four nuclear-OXPHOS input queries are enriched. Within excitatory neurons, 14 eligible fine-cell DEG queries contain 123 mtDNA-OXPHOS occurrences, all upregulated, and 12 of the 14 KDA input queries are enriched.",
      boundary:
        "The percentages describe repeated gene-by-fine-cell DEG occurrences, not expression magnitude or the percentage of unique genes. The nuclear result is weaker than the mtDNA result because fewer input queries are enriched. Enrichment describes the KDA input query and does not count genes returned from KDA calls.",
      transition: "Ask whether the primary mtDNA-OXPHOS pattern appears in SEA-AD.",
    }),
  ],
  [
    45,
    notes({
      goal: "Show the matched SEA-AD evidence for the primary mtDNA-OXPHOS result.",
      walkthrough:
        "Only one matched female epsilon-3 homozygous excitatory-neuron KDA call was evaluable in SEA-AD. Its effective query contains 10 genes. Nine are the same mtDNA-OXPHOS genes found in ROSMAP, and all nine are upregulated in the disease group in both cohorts. The analysis observed nine shared genes compared with 3.83 expected under the category-specific background model. The overlap remains significant after correction, with a Benjamini-Hochberg-adjusted P value of 0.005.",
      boundary:
        "This slide supports the mtDNA component of Finding 1. It does not establish cross-cohort replication of the secondary nuclear-OXPHOS increase. Coverage remains limited to one matched excitatory-neuron KDA call.",
      transition: "Explain why the repeated mitochondrial response may matter biologically.",
    }),
  ],
  [
    46,
    notes({
      goal: "Explain the biological interpretation while keeping the two evidence levels separate.",
      walkthrough:
        "Excitatory neurons use substantial energy to generate and recover from electrical signaling. Mitochondrial DNA encodes 13 core OXPHOS subunits needed by the respiratory system. Their RNA repeatedly increases in ROSMAP and shows the same direction in the matched SEA-AD comparison. Nuclear OXPHOS RNA also mostly increases in ROSMAP, which suggests a broader response, but that secondary component has less enrichment support and no matched SEA-AD confirmation here.",
      boundary:
        "RNA direction alone cannot distinguish successful compensation from mitochondrial stress, altered RNA processing, selective cell survival, or another disease-associated change. It does not show that mitochondria make more ATP or establish a causal mechanism.",
      transition: "Place the result in prior research and clarify what remains unproven.",
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

function relationshipAttributes(tag) {
  return Object.fromEntries(
    [...tag.matchAll(/([A-Za-z:]+)="([^"]*)"/g)].map((match) => [match[1], match[2]]),
  );
}

async function visibleSlidePart(zip, ordinal) {
  const presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  const presentationRels = await zip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  if (!presentationXml || !presentationRels) {
    throw new Error("Presentation ordering metadata is missing");
  }
  const slideIds = [...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g)]
    .map((match) => match[1]);
  const relationshipId = slideIds[ordinal - 1];
  if (!relationshipId) throw new Error(`Visible slide ${ordinal} was not found`);
  const relationships = [...presentationRels.matchAll(/<Relationship\b[^>]*\/?\s*>/g)]
    .map((match) => relationshipAttributes(match[0]));
  const relation = relationships.find(
    (item) => item.Id === relationshipId && item.Type?.endsWith("/slide"),
  );
  if (!relation?.Target) throw new Error(`Slide relationship ${relationshipId} was not found`);
  return relation.Target.startsWith("/")
    ? relation.Target.slice(1)
    : path.posix.normalize(path.posix.join("ppt", relation.Target));
}

async function notesPartForSlide(zip, slidePart) {
  const relsPath = path.posix.join(
    path.posix.dirname(slidePart),
    "_rels",
    `${path.posix.basename(slidePart)}.rels`,
  );
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing slide relationships: ${relsPath}`);
  const relationships = [...relsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)]
    .map((match) => relationshipAttributes(match[0]));
  const relation = relationships.find((item) => item.Type?.endsWith("/notesSlide"));
  if (!relation?.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return relation.Target.startsWith("/")
    ? relation.Target.slice(1)
    : path.posix.normalize(path.posix.join(path.posix.dirname(slidePart), relation.Target));
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

  const beforePngs = new Map();
  for (const slideNumber of VISIBLE_SLIDES) {
    const png = await blobBuffer(
      await presentation.export({ slide: slides[slideNumber - 1], format: "png", scale: 2 }),
    );
    beforePngs.set(slideNumber, png);
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-before.png`), png);
  }

  const snapshot = await presentation.inspect({
    kind: "textbox",
    include: "id,slide,name,text,bbox",
    maxChars: 4000000,
  });
  const records = parseNdjson(snapshot.ndjson).filter(
    (record) => record.kind === "textbox" && typeof record.text === "string",
  );
  for (const update of TEXT_UPDATES) {
    const matches = records.filter(
      (record) => record.slide === update.slide && record.name === update.name,
    );
    if (matches.length !== 1) {
      throw new Error(
        `Expected one ${update.name} on slide ${update.slide}, found ${matches.length}`,
      );
    }
    const shape = presentation.resolve(matches[0].id);
    shape.text = update.text;
    if (update.position) shape.position = update.position;
  }

  for (const [slideNumber, updatedNotes] of NOTES_BY_SLIDE) {
    const slide = slides[slideNumber - 1];
    slide.speakerNotes.textFrame.setText(updatedNotes);
    slide.speakerNotes.setVisible(true);
  }

  for (const slideNumber of VISIBLE_SLIDES) {
    const png = await blobBuffer(
      await presentation.export({ slide: slides[slideNumber - 1], format: "png", scale: 2 }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-after.png`), png);
    if (sha256(beforePngs.get(slideNumber)) === sha256(png)) {
      throw new Error(`Visible slide ${slideNumber} did not change`);
    }
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  const currentSourceBuffer = await fs.readFile(SOURCE);
  if (sha256(currentSourceBuffer) !== sourceHash) {
    throw new Error("The source presentation changed during the edit");
  }

  const sourceZip = await JSZip.loadAsync(currentSourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const changedParts = new Set();
  for (const slideNumber of VISIBLE_SLIDES) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const revisedSlideXml = await artifactZip.file(artifactSlidePart)?.async("string");
    if (!revisedSlideXml) throw new Error(`Missing revised slide XML for slide ${slideNumber}`);
    sourceZip.file(sourceSlidePart, revisedSlideXml);
    changedParts.add(sourceSlidePart);
  }
  for (const slideNumber of NOTES_BY_SLIDE.keys()) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const revisedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!revisedNotesXml) throw new Error(`Missing revised notes XML for slide ${slideNumber}`);
    sourceZip.file(sourceNotesPart, revisedNotesXml);
    changedParts.add(sourceNotesPart);
  }

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
    requiredNativeChartOwnerSlides: [13],
    requiredEmbeddedWorkbookChartOwnerSlides: [13],
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
    receiptPath: path.join(BUILD_DIR, "finding1-nuclear-oxphos.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const finalSnapshot = await reopened.inspect({
    kind: "textbox,notes",
    include: "id,slide,name,text,bbox",
    maxChars: 4000000,
  });
  const finalRecords = parseNdjson(finalSnapshot.ndjson);
  for (const update of TEXT_UPDATES) {
    const matches = finalRecords.filter(
      (record) =>
        record.kind === "textbox" &&
        record.slide === update.slide &&
        record.name === update.name &&
        record.text === update.text,
    );
    if (matches.length !== 1) {
      throw new Error(`Final text validation failed for slide ${update.slide} ${update.name}`);
    }
  }
  for (const [slideNumber, expectedNotes] of NOTES_BY_SLIDE) {
    const record = finalRecords.find(
      (item) => item.kind === "notes" && item.slide === slideNumber,
    );
    if (record?.text?.trim() !== expectedNotes.trim()) {
      throw new Error(`Final notes validation failed for slide ${slideNumber}`);
    }
  }
  for (const slideNumber of VISIBLE_SLIDES) {
    const finalPng = await blobBuffer(
      await reopened.export({
        slide: reopenedSlides[slideNumber - 1],
        format: "png",
        scale: 2,
      }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-final.png`), finalPng);
    if (sha256(beforePngs.get(slideNumber)) === sha256(finalPng)) {
      throw new Error(`Final slide ${slideNumber} did not change visually`);
    }
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const sourceFiles = Object.keys(originalZip.files)
    .filter((name) => !originalZip.files[name].dir)
    .sort();
  const actualChangedParts = [];
  for (const name of sourceFiles) {
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [sourceData, finalData] = await Promise.all([
      originalZip.file(name).async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(sourceData) !== sha256(finalData)) actualChangedParts.push(name);
  }
  const expectedChangedParts = [...changedParts].sort();
  if (
    actualChangedParts.length !== expectedChangedParts.length ||
    actualChangedParts.some((part, index) => part !== expectedChangedParts[index])
  ) {
    throw new Error(`Unexpected package changes: ${actualChangedParts.join(", ")}`);
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        slideCount: EXPECTED_SLIDES,
        updatedSlides: VISIBLE_SLIDES,
        changedParts: actualChangedParts,
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
