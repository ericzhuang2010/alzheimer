#!/usr/bin/env node

/** Update only slide 57 speaker notes after the user revised the slide. */

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
  "results/presentations/09162026_slide57_notes_20260922_v1/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slide57_notes_20260922_v1/output/09162026_sex_apoe_kda_fine_broad_slide57_notes_refreshed_20260922_v1.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "cce6ff77da324a65cd3f5b2b50f2d976e1ed6a2580bcee5497106b40e8e48cdc";
const SLIDE_COUNT = 160;
const SLIDE_NUMBER = 57;

const NOTES = [
  "Findings 7, 10, and 17 receive lower priority only because this presentation focuses on differences among sex/APOE groups.",
  "",
  "For Findings 7 and 10, “found across all six sex/APOE groups” means that the related pattern was present in one or more KDA calls for each of the six groups. It does not mean that every individual fine-cell KDA call returned the same genes.",
  "",
  "Finding 7 links RPL11, RPS15, and related genes that help ribosomes outside mitochondria make proteins with nuclear-encoded OXPHOS genes.",
  "",
  "Finding 10 links SELENOM with genes used for mitochondrial protein production. SELENOM helps control oxidative stress and calcium inside the endoplasmic reticulum, the cellular compartment where many proteins are processed.",
  "",
  "Finding 17 provides supporting validation by comparing ROSMAP with SEA-AD. The cohorts agree more clearly on mitochondrial gene-set patterns than on the exact genes returned from KDA calls.",
  "",
  "These findings may still be biologically important or useful as supporting evidence. They simply do not identify a distinct sex/APOE group.",
  "",
  "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 7, 10, and 17.",
].join("\n");

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

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

function parseNdjson(ndjson) {
  return (ndjson || "")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

async function main() {
  if (await fs.stat(FINAL_PPTX).catch(() => undefined)) {
    throw new Error(`Output already exists: ${FINAL_PPTX}`);
  }
  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });

  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceHash = sha256(sourceBuffer);
  if (sourceHash !== EXPECTED_SOURCE_SHA256) {
    throw new Error(`Source deck changed before the notes edit: ${sourceHash}`);
  }

  const { importRuntimeModule } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href
  );
  const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");
  const JSZipModule = await importRuntimeModule("jszip");
  const JSZip = JSZipModule.default ?? JSZipModule;
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const slides = slidesFromPresentation(presentation);
  if (slides.length !== SLIDE_COUNT) {
    throw new Error(`Expected ${SLIDE_COUNT} slides, found ${slides.length}`);
  }

  const slide = slides[SLIDE_NUMBER - 1];
  slide.speakerNotes.textFrame.setText(NOTES);
  slide.speakerNotes.setVisible(true);

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);

  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed during the notes edit");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const notesPart = `ppt/notesSlides/notesSlide${SLIDE_NUMBER}.xml`;
  const notesXml = await artifactZip.file(notesPart)?.async("string");
  if (!notesXml) throw new Error(`Artifact candidate is missing ${notesPart}`);
  sourceZip.file(notesPart, notesXml);

  const hybridCandidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    hybridCandidatePath,
    await sourceZip.generateAsync({
      type: "nodebuffer",
      compression: "DEFLATE",
      compressionOptions: { level: 6 },
    }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  await finalizePresentation({
    explicitTotalSlideCount: SLIDE_COUNT,
    requiredNativeTableOwnerSlides: [53, 54, 55, 56, 57],
    requiredNativeChartOwnerSlides: [19],
    requiredEmbeddedWorkbookChartOwnerSlides: [19],
    nativeChartTargetApplication: "powerpoint",
    workspaceDir: WORKSPACE_DIR,
    candidatePath: hybridCandidatePath,
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
      ...[53, 54, 55, 56, 57].flatMap((number) => [
        "--require-native-table-slide",
        String(number),
      ]),
    ],
    fontPolicy: {
      basis: "reference",
      families: ["Arial"],
      referencePath: SOURCE,
      referenceSha256: sourceHash,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD_DIR, "slide57_notes.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalNotes = parseNdjson(
    (await reopened.inspect({ kind: "notes", maxChars: 5000000 })).ndjson,
  );
  const slide57Notes = finalNotes.find(
    (record) => record.kind === "notes" && record.slide === SLIDE_NUMBER,
  )?.text;
  if (slide57Notes?.trim() !== NOTES.trim()) {
    throw new Error("Speaker notes do not match on slide 57");
  }

  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const changedParts = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) changedParts.push(name);
  }
  changedParts.sort();
  if (changedParts.length !== 1 || changedParts[0] !== notesPart) {
    throw new Error(`Unexpected package changes: ${changedParts.join(", ")}`);
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
        updatedSlides: [SLIDE_NUMBER],
        changedParts,
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
