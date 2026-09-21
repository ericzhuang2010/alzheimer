#!/usr/bin/env node

/** Refresh slide 58 speaker notes after the visible slide was revised. */

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
  "results/presentations/09162026_slide58_notes_refresh_20260920_v2/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slide58_notes_refresh_20260920_v2/output/09162026_sex_apoe_kda_fine_broad_slide58_notes_refreshed_20260920_v2.pptx",
);
const EXPECTED_SLIDES = 159;
const EXPECTED_SOURCE_SHA256 =
  "a434b6b070dbb4f275b848ba74789cabacd09f4573103ec1e22fc5152a524322";
const SLIDE_NUMBER = 58;

const UPDATED_NOTES = [
  "Teaching goal: Quantify the ROSMAP DEG-occurrence pattern for Finding 3.",
  "",
  "Walk through: Each KDA input query starts with significant DEGs from one fine-cell and sex/APOE comparison, retains the MitoCarta MT genes, and then retains genes available in the relevant network. Across the eligible female APOE ε2 KDA input queries, core MT genes contribute 128 DEG occurrences: 127 AD-up and one AD-down, so 99 percent are upregulated. Nuclear-encoded OXPHOS genes contribute 243 occurrences: 239 AD-up and four AD-down, so 98 percent are upregulated. One occurrence means that one gene appears as a DEG in one eligible query. The same gene can contribute another occurrence in another fine-cell query.",
  "",
  "Scientific boundary: The numbers 128 and 243 are gene-by-query occurrences, not counts of unique genes, cells, or donors. The phrase ‘across eligible KDA calls’ refers to the DEG input queries used to make those calls. It does not refer to genes returned from KDA calls. These percentages also do not measure expression magnitude, OXPHOS protein abundance, respiration, or ATP production.",
  "",
  "Transition: Compare this primary fine-cell pattern with the direct broad-cell ROSMAP result and the available SEA-AD coverage.",
  "",
  "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 3 and Section 2.2. Literature: https://doi.org/10.1016/j.neuron.2019.03.075; https://doi.org/10.1016/j.celrep.2023.113183; https://doi.org/10.1186/s13024-023-00624-5",
].join("\n");

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

  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceHash = sha256(sourceBuffer);
  if (sourceHash !== EXPECTED_SOURCE_SHA256) {
    throw new Error(`Source deck changed before the notes refresh: ${sourceHash}`);
  }

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

  const sourceSnapshot = await presentation.inspect({
    kind: "slide,textbox,notes",
    maxChars: 4000000,
  });
  const slide58Records = sourceSnapshot.ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .filter((record) => record.slide === SLIDE_NUMBER);
  if (!slide58Records.some((record) => record.kind === "slide")) {
    throw new Error("Could not inspect slide 58");
  }
  await fs.writeFile(
    path.join(BUILD_DIR, "slide-58-before.inspect.ndjson"),
    slide58Records.map((record) => JSON.stringify(record)).join("\n") + "\n",
    "utf8",
  );

  const beforePng = await blobBuffer(
    await presentation.export({ slide: slides[SLIDE_NUMBER - 1], format: "png", scale: 1.5 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-58-before.png"), beforePng);
  slides[SLIDE_NUMBER - 1].speakerNotes.textFrame.setText(UPDATED_NOTES);
  slides[SLIDE_NUMBER - 1].speakerNotes.setVisible(true);
  const afterPng = await blobBuffer(
    await presentation.export({ slide: slides[SLIDE_NUMBER - 1], format: "png", scale: 1.5 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-58-after.png"), afterPng);
  if (sha256(beforePng) !== sha256(afterPng)) {
    throw new Error("Visible slide 58 changed while updating speaker notes");
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed during the notes refresh");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const sourceSlidePart = await visibleSlidePart(sourceZip, SLIDE_NUMBER);
  const artifactSlidePart = await visibleSlidePart(artifactZip, SLIDE_NUMBER);
  const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
  const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
  const updatedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
  if (!updatedNotesXml?.includes("The phrase ‘across eligible KDA calls’")) {
    throw new Error("Artifact candidate does not contain the revised slide 58 notes");
  }
  sourceZip.file(sourceNotesPart, updatedNotesXml);
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
    receiptPath: path.join(BUILD_DIR, "slide58_notes_refresh_v2.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const finalPng = await blobBuffer(
    await reopened.export({
      slide: reopenedSlides[SLIDE_NUMBER - 1],
      format: "png",
      scale: 1.5,
    }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-58-final.png"), finalPng);
  if (sha256(beforePng) !== sha256(finalPng)) {
    throw new Error("Finalized deck changed visible slide 58");
  }
  const finalNotes = await reopened.inspect({ kind: "notes", maxChars: 3000000 });
  const finalSlide58Notes = finalNotes.ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .find((record) => record.kind === "notes" && record.slide === SLIDE_NUMBER)?.text;
  if (finalSlide58Notes?.trim() !== UPDATED_NOTES.trim()) {
    throw new Error("Finalized slide 58 notes do not match the revision");
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
    const [before, after] = await Promise.all([
      originalZip.file(name).async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) changedParts.push(name);
  }
  if (changedParts.length !== 1 || changedParts[0] !== sourceNotesPart) {
    throw new Error(`Unexpected package changes: ${changedParts.join(", ")}`);
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
        slideCount: EXPECTED_SLIDES,
        updatedSlide: SLIDE_NUMBER,
        visibleSlidePreserved: true,
        changedParts,
        warnings: validation.warnings ?? [],
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
