#!/usr/bin/env node

/** Refresh speaker notes for the user-revised slides 6 and 7. */

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
  "results/presentations/09162026_slides6_7_script_refresh_20260920/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slides6_7_script_refresh_20260920/output/09162026_sex_apoe_kda_fine_broad_slides6_7_notes_refreshed_20260920.pptx",
);
const EXPECTED_SLIDES = 160;

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
    6,
    notes({
      goal: "Define the two mitochondrial protein-gene sets used throughout the study.",
      walkthrough:
        "Start with core MT genes. In this study, that term means the 13 protein-coding genes in mitochondrial DNA. All 13 encode structural subunits of oxidative phosphorylation, or OXPHOS. The broader MitoCarta MT inventory contains 1,136 protein-coding genes associated with mitochondria. It includes the same 13 core MT genes and 1,123 genes encoded by nuclear DNA. We use MitoCarta MT genes to define the mitochondrial pathways and to build the DEG input queries used when we make KDA calls.",
      boundary:
        "Mitochondrial DNA contains 37 genes in total. The other 24 encode 22 transfer RNAs and two ribosomal RNAs, so they are not included in the protein-gene sets analyzed here. In this study, core MT genes and mtDNA-encoded structural OXPHOS genes refer to the same 13 genes. Expression of these genes does not measure mtDNA copy number, OXPHOS protein abundance, or mitochondrial function.",
      transition:
        "The next slide shows how the 13 core MT genes and the nuclear-encoded OXPHOS genes fit inside MitoCarta.",
    }),
  ],
  [
    7,
    notes({
      goal:
        "Show how the structural OXPHOS gene set is contained within the MitoCarta MT inventory.",
      walkthrough:
        "The green outer circle contains all 1,136 MitoCarta MT genes. The gold inner circle sits fully inside it because all 99 structural OXPHOS genes used here are in MitoCarta. The vertical split separates the 13 core MT genes, encoded by mitochondrial DNA, from 86 OXPHOS genes encoded by nuclear DNA. Together, the two groups account for the 99 structural OXPHOS genes. The remaining 1,037 MitoCarta MT genes fall outside the structural OXPHOS set.",
      boundary:
        "The circles show gene-set membership only. Nuclear-encoded tells us that the gene is located in nuclear DNA. Its protein still functions in mitochondria. The diagram does not show expression direction, pathway enrichment, protein abundance, or mitochondrial function. Circle area does not represent gene count.",
      transition:
        "Next, introduce the three levels used to organize MitoCarta pathways.",
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

  const expectedTitles = new Map([
    [6, "Two mitochondrial gene sets used in this study"],
    [7, "How the OXPHOS gene sets fit within MitoCarta"],
  ]);
  const titleSnapshot = await presentation.inspect({
    kind: "slide,textbox,notes",
    maxChars: 200000,
  });
  const titlesBySlide = new Map(
    titleSnapshot.ndjson
      .split("\n")
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .filter((record) => record.kind === "slide" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.title]),
  );
  for (const [slideNumber, expectedTitle] of expectedTitles) {
    if (titlesBySlide.get(slideNumber) !== expectedTitle) {
      throw new Error(
        `Slide ${slideNumber} title mismatch: ${JSON.stringify(titlesBySlide.get(slideNumber))}`,
      );
    }
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
      referenceSha256: sha256(sourceBuffer),
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD_DIR, "slides6_7_notes_refreshed.validation.json"),
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
