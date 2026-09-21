#!/usr/bin/env node

/** Refresh speaker notes for the revised slide 12 and slides 50–55. */

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
  "results/presentations/09162026_slides12_50_55_script_refresh_20260920/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slides12_50_55_script_refresh_20260920/output/09162026_sex_apoe_kda_fine_broad_slides12_50_55_notes_refreshed_20260920.pptx",
);
const EXPECTED_SLIDES = 159;

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
    12,
    notes({
      goal:
        "Define a DEG occurrence and show how the upregulated OXPHOS occurrence percentage is calculated.",
      walkthrough:
        "Start with the red definition. One occurrence means that one pathway gene is a significant DEG in one fine-cell comparison. If the same gene is significant in another fine cell type, it contributes another occurrence. Calculate the percentage separately for each sex/APOE group and each OXPHOS gene set. Divide the upregulated occurrences by all upregulated plus downregulated occurrences, then multiply by 100. In the male epsilon-3 homozygous mtDNA-encoded OXPHOS example, 70 occurrences were upregulated and 11 were downregulated. Seventy divided by 81 equals 86 percent upregulated. A value of 50 percent means that upregulated and downregulated occurrences are equally common. Values above 50 percent favor upregulation, while values below 50 percent favor downregulation.",
      boundary:
        "This occurrence-based summary gives more weight to genes that recur across fine-cell comparisons. It is not a fold change, a percentage of unique genes, cells, donors, or fine cell types, an enrichment result, or a measure of OXPHOS activity. Repeated occurrences are not independent biological replications.",
      transition:
        "Compare the upregulated occurrence percentage across the six sex/APOE groups.",
    }),
  ],
  [
    50,
    notes({
      goal:
        "Present the ROSMAP evidence for opposite OXPHOS directions in male epsilon-3 homozygous cells.",
      walkthrough:
        "Across 31 eligible male epsilon-3 homozygous fine-cell DEG queries used to make KDA calls, mtDNA-encoded OXPHOS genes contributed 81 occurrences: 70 AD-up and 11 AD-down. Therefore, 86 percent were upregulated. Nuclear-encoded OXPHOS genes contributed 68 occurrences: 8 AD-up and 60 AD-down. Therefore, 88 percent were downregulated. An occurrence is one pathway gene identified as a DEG in one fine-cell comparison, so the same gene can contribute again in another fine cell type.",
      boundary:
        "These are occurrences among the mitochondrial DEG input queries, not unique genes, independent donors, or genes returned from KDA calls. Opposite directions in gene expression do not demonstrate mismatched proteins or impaired respiration.",
      transition:
        "Ask whether the matched male epsilon-3 homozygous inhibitory-neuron pattern appears in SEA-AD.",
    }),
  ],
  [
    51,
    notes({
      goal:
        "Explain the matched SEA-AD support and what program-level agreement means here.",
      walkthrough:
        "Eight matched male epsilon-3 homozygous inhibitory-neuron KDA calls were evaluable. ROSMAP and SEA-AD shared 22 mitochondrial-query genes, and 19 of the 22 had the same AD direction. Nine mtDNA-encoded OXPHOS genes were upregulated in both cohorts. Nuclear-encoded OXPHOS, protein-import, mitochondrial-ribosome, and maintenance genes were downregulated in both. The overlap was 22 genes compared with 15.17 expected and remained significant after correction, with a Benjamini-Hochberg adjusted P value of 0.0417. Excluding unresolved mitochondrial identity-conflict genes left 21 shared genes and a similar adjusted P value of 0.0486. Program-level support means agreement among related input DEG genes and their directions, not replication of the same gene returned from a KDA call.",
      boundary:
        "This is focused cross-cohort support within the matched inhibitory-neuron context. It does not establish the same gene returned from KDA calls, protein-level imbalance, mitochondrial dysfunction, or a formal disease-by-sex-by-APOE interaction.",
      transition:
        "Identify the genes that account for the cross-cohort directional agreement.",
    }),
  ],
  [
    52,
    notes({
      goal:
        "Name the concordant and discordant genes in the matched inhibitory-neuron comparison.",
      walkthrough:
        "Nine mtDNA-encoded OXPHOS genes were upregulated in both cohorts: MT-ATP6, MT-CO2, MT-CO3, MT-CYB, MT-ND1, MT-ND2, MT-ND3, MT-ND4, and MT-ND4L. Eight nuclear or mitochondrial-maintenance genes were downregulated in both: UQCRFS1, SLC25A5, TIMM13, TIMM17A, MRPL16, MRPS34, ENDOG, and MTCH1. DBP was also downregulated in both cohorts, while PRELID2 was upregulated in both. HIBCH, ISCU, and TMEM126B had opposite directions across cohorts.",
      boundary:
        "These directions describe shared mitochondrial-query DEGs rather than genes returned from KDA calls. Directional agreement does not establish matched protein abundance, respiratory-complex assembly, or mitochondrial function.",
      transition:
        "Explain why coordinated expression from two genomes and their support systems may matter.",
    }),
  ],
  [
    53,
    notes({
      goal:
        "Explain the biological relevance of the two-genome pattern without claiming impaired function.",
      walkthrough:
        "OXPHOS complexes combine proteins encoded by mitochondrial DNA with proteins encoded by nuclear DNA, so the two gene sets ultimately contribute to the same respiratory system. The cross-cohort evidence also includes lower expression of genes involved in mitochondrial protein import, mitochondrial ribosomes, transport, and maintenance. Opposite expression directions could reflect compensation, unassembled components, an altered cell state, or mitochondrial stress, but the present data cannot distinguish among those possibilities.",
      boundary:
        "This is an RNA-level difference between two OXPHOS gene sets. It does not show that respiratory proteins, complex assembly, respiration, or ATP production are unbalanced. The possible explanations are hypotheses for follow-up.",
      transition:
        "Place the finding in prior mitonuclear and cell-resolved Alzheimer’s research.",
    }),
  ],
  [
    54,
    notes({
      goal:
        "Connect the finding to prior research while preserving the evidence and novelty boundaries.",
      walkthrough:
        "General mitonuclear biology establishes that OXPHOS requires coordinated mitochondrial-encoded and nuclear-encoded parts, but it does not show a protein imbalance in these samples. Guo and colleagues support analyzing Alzheimer’s molecular networks separately by sex, but they do not test this exact male epsilon-3 homozygous mismatch. Mathys and colleagues support strong cell-resolved Alzheimer’s responses, but their study also uses ROSMAP and therefore does not provide independent replication. The novelty assessment is high because the biological concept is established while this cross-cohort male epsilon-3 homozygous inhibitory-neuron pattern was not identified in the reviewed literature.",
      boundary:
        "Plausibility and novelty are separate from proof. None of these sources independently establishes the exact subgroup pattern, protein imbalance, or mitochondrial dysfunction.",
      transition:
        "Proceed to Finding 3, where both OXPHOS gene sets increase in female epsilon-2 cells.",
    }),
  ],
  [
    55,
    notes({
      goal: "Introduce Finding 3 and distinguish it from the male epsilon-3 homozygous mismatch.",
      walkthrough:
        "Finding 3 focuses on female APOE epsilon-2 cells. In these cells, both mtDNA-encoded and nuclear-encoded OXPHOS genes were mostly upregulated in Alzheimer’s disease. The two gene sets therefore moved in the same direction, unlike the opposing directions in Finding 2. The next slides show the plain-language result, the ROSMAP evidence, the supporting context, and the limits of interpretation.",
      boundary:
        "This coordinated pathway-level expression pattern does not establish greater OXPHOS protein abundance, increased ATP production, improved mitochondrial function, or a female epsilon-2-specific interaction.",
      transition: "State Finding 3 in plain language.",
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
  for (const [slideNumber, updatedNotes] of NOTES_BY_SLIDE) {
    const slide = slides[slideNumber - 1];
    const beforePng = await blobBuffer(
      await presentation.export({ slide, format: "png", scale: 2 }),
    );
    beforePngs.set(slideNumber, beforePng);
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-before.png`), beforePng);
    slide.speakerNotes.textFrame.setText(updatedNotes);
    slide.speakerNotes.setVisible(true);
    const afterPng = await blobBuffer(
      await presentation.export({ slide, format: "png", scale: 2 }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-after.png`), afterPng);
    if (sha256(beforePng) !== sha256(afterPng)) {
      throw new Error(`Visible slide ${slideNumber} changed while updating notes`);
    }
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const changedNotesParts = [];
  for (const slideNumber of NOTES_BY_SLIDE.keys()) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const updatedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!updatedNotesXml) throw new Error(`Updated notes are missing for slide ${slideNumber}`);
    sourceZip.file(sourceNotesPart, updatedNotesXml);
    changedNotesParts.push(sourceNotesPart);
  }

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
    await sourceZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const result = await finalizePresentation({
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
      referenceSha256: sha256(sourceBuffer),
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(
      BUILD_DIR,
      "09162026_sex_apoe_kda_fine_broad_slides12_50_55_notes_refreshed.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const notesSnapshot = await reopened.inspect({ kind: "notes", maxChars: 2000000 });
  const finalNotesBySlide = new Map(
    notesSnapshot.ndjson
      .split("\n")
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text]),
  );
  for (const [slideNumber, expectedNotes] of NOTES_BY_SLIDE) {
    const finalPng = await blobBuffer(
      await reopened.export({
        slide: reopenedSlides[slideNumber - 1],
        format: "png",
        scale: 2,
      }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-final.png`), finalPng);
    if (sha256(beforePngs.get(slideNumber)) !== sha256(finalPng)) {
      throw new Error(`Finalized deck changed visible slide ${slideNumber}`);
    }
    const actualNotes = finalNotesBySlide.get(slideNumber);
    if (typeof actualNotes !== "string") {
      throw new Error(`Finalized notes are missing on slide ${slideNumber}`);
    }
    if (actualNotes.trim() !== expectedNotes.trim()) {
      throw new Error(`Finalized notes do not match on slide ${slideNumber}`);
    }
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const sourceFiles = Object.keys(originalZip.files)
    .filter((name) => !originalZip.files[name].dir)
    .sort();
  const changedParts = [];
  for (const name of sourceFiles) {
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [sourceData, finalData] = await Promise.all([
      originalZip.file(name).async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(sourceData) !== sha256(finalData)) changedParts.push(name);
  }
  const expectedParts = [...changedNotesParts].sort();
  if (
    changedParts.length !== expectedParts.length ||
    changedParts.some((part, index) => part !== expectedParts[index])
  ) {
    throw new Error(`Unexpected package changes: ${changedParts.join(", ")}`);
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sha256(sourceBuffer),
        output: FINAL_PPTX,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
        slideCount: EXPECTED_SLIDES,
        updatedSlides: [...NOTES_BY_SLIDE.keys()],
        changedPackageParts: changedParts,
        warnings: result.warnings ?? [],
      },
      null,
      2,
    ),
  );
}

await main();
